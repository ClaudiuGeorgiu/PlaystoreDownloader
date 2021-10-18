import logging

import requests

logger = logging.getLogger(__name__)


class PackageMeta:
    def __init__(self, api, package_name) -> None:
        self.api = api
        self.package_name = package_name
        self.details = self.app_details()
        if not self.details:
            exception = RuntimeError(
                "Can't proceed with the download: there was an error when "
                f"requesting details for app '{self.package_name}'"
            )
            logging.exception(exception)
            raise exception

    def app_details(self) -> object:
        """
        Get the details for a certain app (identified by the package name) in the
        Google Play Store.

        :param package_name: The package name of the app (e.g., "com.example.myapp").
        :return: A protobuf object containing the details of the app. The result
                    will be None if there was something wrong with the query.
        """

        # Prepare the query.
        path = "details"
        query = {"doc": requests.utils.quote(self.package_name)}

        # Execute the query.
        response = self.api._execute_request(path, query)

        # If the query went completely wrong.
        try:
            return response.payload.detailsResponse
        except AttributeError as no_payload_error:
            try:
                logger.error(
                    f"Error for app '{self.package_name}': "
                    f"{response.commands.displayErrorMessage}"
                )
                raise no_payload_error
            except AttributeError as no_commands_error:
                logger.error(
                    f"There was an error when requesting details for "
                    f"app '{self.package_name}'"
                )
                raise no_commands_error from no_payload_error

    def __getattr__(self, name: str):
        return getattr(self.details, name)
