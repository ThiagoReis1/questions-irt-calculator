import logging
from os import listdir, path

from codebench_analytics.model.codebench_types import Data, Resource

logger = logging.getLogger(__name__)


class Components:
    """Returns elements sources from each class, which can be assessments
    or users (students).
    """

    @staticmethod
    def get_data(dataset_src: str, resource: Resource) -> list:
        classes = listdir(dataset_src)
        data = []

        for _class in classes:
            src = path.join(dataset_src, _class, resource.value)
            rlsrc = path.relpath(src, dataset_src)
            try:
                for element in listdir(src):
                    data.append(path.join(rlsrc, element))
            except FileNotFoundError:
                logger.error(
                    "resource '%s' not found in path '%s'", resource.value, src
                )

        return data

    @staticmethod
    def get_users_data(dataset_src: str, resource: Resource) -> dict:
        users = Components.get_data(dataset_src, Data.USER)
        students = {}

        for user_path in users:
            d = user_path.split("/")
            class_id, user_id = d[0], d[-1]
            key = f"{class_id}-{user_id}"

            assert key not in students, "Duplicated entry for user %d" % user_id

            src = path.join(dataset_src, user_path, resource.value)

            if path.isfile(src):
                students[key] = path.relpath(src, dataset_src)
                continue

            students[key] = []
            for filename in listdir(src):
                fullpath = path.join(src, filename)
                students[key].append(path.relpath(fullpath, dataset_src))

        return students


# For testing purposes only
if __name__ == "__main__":
    d = Components.get_users_data(
        "/home/jackson/Documentos/UFAM/8_Periodo/TCC/Dataset/collection/2017-1",
        Resource.EXECUTIONS,
    )
    print(d)
