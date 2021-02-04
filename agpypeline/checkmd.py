"""CheckMD Class"""

from typing import List, NamedTuple, Optional, TextIO


# pylint: disable=invalid-name
class CheckMD(NamedTuple):
    """This is the CheckMD class based off of NamedTuple which can be used in
    order to store data passed into argparse."""
    timestamp: str
    season: str
    experiment: str
    list_files: List[TextIO]
    working_folder: str
    container_name: Optional[str] = None
    target_container_name: Optional[str] = None
    trigger_name: Optional[str] = None
    context_md: Optional[str] = None

    def get_list_files(self):
        """Returns list_files"""
        return self.list_files

    def get_working_folder(self):
        """Returns working_folder"""
        return self.working_folder
