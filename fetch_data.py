from typing import List, Dict, Tuple, Union
from copy import deepcopy
from requests import request
from hashlib import sha256
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
        self.matchs_hash_dict : Dict[str, Dict[str, str]] = dict()
        self.actions_hash_dict : Dict[str, List[str]] = dict()
        self.flow_hash_dict : Dict[str, Dict[str, str]] = dict()
        self.database: List[Dict] = (dict(), dict(), dict())


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
        switches_response : list[Dict] = request("GET", switch_url).json()
        dpids:list[int] = [int(switch['dpid']) for switch in switches_response]

        return dpids


    def get_flow_match_action(self, uri: str = "stats/flow/") -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]], Dict[str, List[str]]]:
        """
        Fetches the flow rules for a specific switch identified by its DPID.

        Args:
            uri (str): The URI to fetch the flow rules.

        Returns:
            Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]], Dict[str, List[str]]]: A tuple containing three dictionaries:
                - flow_hash_dict: A dictionary containing the flow hashes.
                - matchs_hash_dict: A dictionary containing the match hashes.
                - actions_hash_dict: A dictionary containing the action hashes.
        """

        flow_url: str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        dpids: List[int] = self.get_dpids()

        for dpid in dpids:
            switch_flow_url: str = f"{flow_url}{dpid}"
            flow_response: Dict = request("GET", switch_flow_url).json()
            flow_entries : List[Dict] = flow_response[str(dpid)]
            
            for flow_entry in flow_entries:
                match_labels: Dict[str, Union[str, int]] = dict(sorted(flow_entry['match'].items()))
                action_labels: List[str] = flow_entry['actions']

                match_encode:bytes = str(match_labels).encode('utf-8')
                action_encode:bytes = str(action_labels).encode('utf-8')
                priority_encode:bytes = str(flow_entry['priority']).encode('utf-8')
                table_id_encode:bytes = str(flow_entry['table_id']).encode('utf-8')

                match_hash: str = sha256(match_encode).hexdigest()
                action_hash: str = sha256(action_encode).hexdigest()

                flow_hash: str = sha256(priority_encode + table_id_encode + match_encode + action_encode).hexdigest()
                
                self.matchs_hash_dict[match_hash] = match_labels
                self.actions_hash_dict[action_hash] = action_labels
                self.flow_hash_dict[flow_hash] = {
                    "match": match_hash,
                    "actions": action_hash
                }

        return (self.flow_hash_dict, self.matchs_hash_dict, self.actions_hash_dict)


    def compare(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Compares the old and new hashes of flow entries.
        This function checks for any changes in the flow entries and prints the differences.

        Returns:
            Tuple[List[str], List[str], List[str]]: A tuple containing three lists:
                - flow_remove: A list of flow hashes that have been removed.
                - match_remove: A list of match hashes that have been removed.
                - action_remove: A list of action hashes that have been removed.
        """

        new_hashes = self.get_flow_match_action()

        flow_hashes, match_hashes, action_hashes = new_hashes
        old_flow_hashes, old_match_hashes, old_action_hashes = self.database

        for key in flow_hashes.keys():
            if old_flow_hashes.get(key):
                old_flow_hashes.pop(key)

        flow_remove: List[str] = list(old_flow_hashes.keys())
        
        for key in match_hashes.keys():
            if old_match_hashes.get(key):
                old_match_hashes.pop(key)

        match_remove: List[str] = list(old_match_hashes.keys())
        
        for key in action_hashes.keys():
            if old_action_hashes.get(key):
                old_action_hashes.pop(key)
            
        action_remove: List[str] = list(old_action_hashes.keys())

        self.database = deepcopy(new_hashes)

        return (flow_remove, match_remove, action_remove)


if __name__ == "__main__":
    HC = Hashcompute()
    dpids: List[int] = HC.get_dpids()
    print(dpids)

    HC.compare()
