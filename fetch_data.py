from typing import List, Dict
import requests
import json

class Hashcompute:
    """
    A class to compute hash values for different data types.
    """

    def __init__(self, base_url: str = "http://localhost:8080/"):
        self.base_url: str = base_url
        self.uris: Dict[str, str] = {
            "switches": "v1.0/topology/switches",
            "flow_stats": "stats/flow/",
            "links": "v1.0/topology/links",
            "hosts": "v1.0/topology/hosts"
        }

    def get_dpids(self, uri : str ="v1.0/topology/switches") -> List[int]:
        """
        Fetches the data of all switches in the network.
        This function sends a GET request to the specified URI and retrieves the DPID of all switches.

        Args:
            uri (str): The URI to fetch the switches.

        Returns:
            list[int]: A list of DPIDs (Data Path Identifiers) of the switches.
        """

        switch_url : str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        switches_response : list[Dict] = requests.request("GET", switch_url).json()
        dpids:list[int] = [int(switch['dpid']) for switch in switches_response]

        return dpids


    def get_flow_match_action(self, uri: str = "stats/flow/") -> Dict:
        """
        Fetches the flow rules for a specific switch identified by its DPID.

        Args:
            uri (str): The URI to fetch the flow rules.

        Returns:
            dict: A dictionary containing the flow hashes and their corresponding match and action hashes.
        """

        flow_url: str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        dpids: List[int] = self.get_dpids()
        hash_dict: Dict[str, Dict[str, str]] = {}

        for dpid in dpids:
            switch_flow_url: str = f"{flow_url}{dpid}"
            flow_response: Dict = requests.request("GET", switch_flow_url).json()
            print(json.dumps(flow_response[str(dpid)], indent=2))

        return hash_dict


if __name__ == "__main__":
    HC = Hashcompute()
    dpids: List[int] = HC.get_dpids()
    print(dpids)

    HC.get_flow_match_action()