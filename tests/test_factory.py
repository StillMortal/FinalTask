# Use only
# python -m pytest tests
# command because
# https://docs.pytest.org/en/latest/explanation/pythonpath.html#invoking-pytest-versus-python-m-pytest


from os import path
from time import sleep

to_monitor_service_specify_the_waiting_time_in_seconds = 3

initial_config = {
    "options": "  web_string:\n"
    "    build: web_string/\n"
    "    restart: unless-stopped\n"
    "    labels:\n"
    "      - traefik.frontend.rule=Host:web-string.net,web-string.com\n"
    "      - traefik.port=81\n"
    "      - traefik.enable=true\n",
}

changed_config = {
    "options": "  web_string:\n"
    "    build: web_string/\n"
    "    restart: always\n"  # <--- change here
    "    labels:\n"
    "      - traefik.frontend.rule=Host:web-string.net,web-string.com\n"
    "      - traefik.port=81\n"
    "      - traefik.enable=true\n",
}


def test_home_page_status(client):
    assert client.get("/").status_code == 200
    assert client.get("/home").status_code == 200


def test_home_page(client):
    response = client.get("/")
    assert b"Home page" in response.data


def test_adding_container_status(client):
    response = client.get("/adding_container")
    assert response.status_code == 200


def test_adding_container_post_data(client):
    data_before_transformation = {
        "path_to_dockerfile": "some_path",
        "options": "web_string:\n"
        "  build: web_string/\n"
        "  restart: unless-stopped\n"
        "  labels:\n"
        "    - traefik.frontend.rule=Host:web-string.net,web-string.com\n"
        "    - traefik.port=81\n"
        "    - traefik.enable=true\n",
        "http_port": "81",
        "url": "web-string.com",
    }

    response = client.post("/adding_container", data=data_before_transformation)

    with open(
        path.dirname(path.dirname(__file__)) + "/flaskr/docker-compose.yaml"
    ) as file:
        assert initial_config["options"] in file.read()

    assert response.headers["Location"] == "http://localhost/"

    sleep(to_monitor_service_specify_the_waiting_time_in_seconds)


def test_depublication_status(client):
    assert client.get("/depublication").status_code == 200


def test_depublication_post_data(client):
    response = client.post("/depublication", data={"name_of_service": "web_string"})

    with open(
        path.dirname(path.dirname(__file__)) + "/flaskr/used_services.txt"
    ) as file:
        assert initial_config["options"] in file.read()

    assert response.headers["Location"] == "http://localhost/"


def test_configuration_of_services_status(client):
    assert client.get("/configuration_of_services").status_code == 200


def test_configuration_of_services_changing_configuration(client):
    assert initial_config["options"] in client.get(
        "/configuration_of_services"
    ).get_data(as_text=True)

    response = client.post(
        "/configuration_of_services",
        data={
            "configuration_of_services": "services\n"
            + changed_config["options"]  # this should be for indentation
        },
    )

    with open(
        path.dirname(path.dirname(__file__)) + "/flaskr/used_services.txt"
    ) as file:
        assert changed_config["options"] in file.read()

    assert response.headers["Location"] == "http://localhost/"


def test_republication_status(client):
    assert client.get("/republication").status_code == 200


def test_republication_post_data(client):
    response = client.post("/republication", data={"name_of_service": "web_string"})

    with open(
        path.dirname(path.dirname(__file__)) + "/flaskr/docker-compose.yaml"
    ) as file:
        assert changed_config["options"] in file.read()

    assert response.headers["Location"] == "http://localhost/"

    sleep(to_monitor_service_specify_the_waiting_time_in_seconds)

    # then we delete everything that we used in the tests
    client.post("/depublication", data={"name_of_service": "web_string"})

    with open(
        path.dirname(path.dirname(__file__)) + "/flaskr/used_services.txt", "w"
    ) as file:
        file.write("services\n")

    with open("/etc/hosts", "r+") as file:
        data = file.read().replace("127.0.0.1 web-string.com\n", "")
        file.seek(0)
        file.write(data)
        file.truncate()
