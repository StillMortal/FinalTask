# Note: all commands below must be run in the terminal.

# first, run traefic from the flaskr folder using
# docker-compose up -d reverse-proxy

# then launch the application from the root of the project using
# export FLASK_APP=flaskr
# export FLASK_ENV=development
# flask run


from os import path
from re import search
from subprocess import call

from flask import Flask, abort, redirect, render_template, request
from werkzeug.wrappers import Response


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    @app.route("/home")
    @app.route("/")
    def index() -> str:
        """The home page.

        Args:

        Returns:
            The home page template.
        """
        return render_template("index.html")

    def start_service(name_of_service: str) -> None:
        """Start docker service.

        Args:
            name_of_service: The name of the service to run.

        Returns:
            None.
        """
        call(
            ["docker-compose", "up", "-d", name_of_service],
            cwd=path.dirname(path.abspath(__file__)),
        )  # works only in the specified directory

    def url_already_exists(url: str) -> bool:
        """Checks if the url is free.

        Args:
            url: The url of the service.

        Returns:
            True if free, False otherwise.
        """
        with open("/etc/hosts") as file:
            if url in file.read():
                return True
        return False

    @app.route("/adding_container", methods=["GET", "POST"])
    def adding_container() -> [str, Response]:
        """Gets the service settings and launches it.

        Args:

        Returns:
            Returns adding a container template if the GET method is used,
            otherwise redirects to the home page.
        """
        if request.method == "GET":
            return render_template("adding_container.html")

        # path_to_dockerfile = request.form["path_to_dockerfile"]  # Not used
        options = request.form["options"]
        # http_port = request.form["http_port"]  # Not used
        url = request.form["url"]

        if url_already_exists(url):
            abort(400, description="The url already exists")

        with open("/etc/hosts", "a") as file:
            file.write("127.0.0.1 " + url + "\n")

        name_of_service = options[: options.index(":")]
        with open(
            path.dirname(path.abspath(__file__)) + "/docker-compose.yaml", "a"
        ) as docker_compose:
            for line in options.strip().split("\n"):
                docker_compose.write("  " + line + "\n")
            docker_compose.write("\n")

        start_service(name_of_service)

        return redirect("/")

    def editing_files(
        name_of_service: str, file_to_search_and_write: str, file_to_append: str
    ) -> None:
        """First, it checks the existence of the service name.
        If the service name exists,
        then it adds information about it to the file_to_append.
        Then it cuts the same information from the file_to_search_and_write.

        Args:
            name_of_service: The name of the service.
            file_to_search_and_write: A filepath for checking the service name
            and overwriting.
            file_to_append: A filepath for adding information about the service.

        Returns:
            None
        """
        with open(file_to_search_and_write, "r") as data:
            data = data.read()
        pattern = "  " + name_of_service + ":[\\d\\D]+?\\n\\n"
        result = search(pattern, data)
        if result is None:
            abort(400, description="Wrong name. The name does not exist")

        span = result.span()
        with open(file_to_append, "a") as file_to_append:
            file_to_append.write(data[span[0] : span[1]])
        with open(file_to_search_and_write, "w") as file_to_write:
            file_to_write.write(data[: span[0]] + data[span[1] :])

    @app.route("/depublication", methods=["GET", "POST"])
    def depublication() -> [str, Response]:
        """First gets the name of the service. Then stops and deletes it.

        Args:

        Returns:
            Returns depublication template if the GET method is used,
            otherwise redirects to the home page.
        """
        if request.method == "GET":
            return render_template("depublication.html")

        name_of_service = request.form["name_of_service"]
        editing_files(
            name_of_service,
            path.dirname(path.abspath(__file__)) + "/docker-compose.yaml",
            path.dirname(path.abspath(__file__)) + "/used_services.txt",
        )

        call(
            [
                "docker",
                "rm",
                "-f",
                path.basename(path.dirname(__file__)) + "_" + name_of_service + "_1",
            ]
        )  # works when service is running
        call(
            [
                "docker",
                "rmi",
                path.basename(path.dirname(__file__)) + "_" + name_of_service,
            ]
        )  # delete image

        return redirect("/")

    @app.route("/republication", methods=["GET", "POST"])
    def republication() -> [str, Response]:
        """First gets the name of the service. Then launches it.

        Args:

        Returns:
            Returns republication template if the GET method is used,
            otherwise redirects to the home page.
        """
        if request.method == "GET":
            return render_template("republication.html")

        name_of_service = request.form["name_of_service"]
        editing_files(
            name_of_service,
            path.dirname(path.abspath(__file__)) + "/used_services.txt",
            path.dirname(path.abspath(__file__)) + "/docker-compose.yaml",
        )

        start_service(name_of_service)

        return redirect("/")

    @app.route("/configuration_of_services", methods=["GET", "POST"])
    def configuration_of_services() -> [str, Response]:
        """Saves the new configuration of services.

        Args:

        Returns:
            Returns configuration of services template if the GET method is used,
            otherwise redirects to the home page.
        """
        if request.method == "GET":
            with open(path.dirname(path.abspath(__file__)) + "/used_services.txt") as f:
                t = f.read()

            return render_template("configuration_of_services.html", t=t)

        with open(
            path.dirname(path.abspath(__file__)) + "/used_services.txt", "w"
        ) as file:
            file.write(request.form["configuration_of_services"].strip() + "\n\n")

        return redirect("/")

    return app
