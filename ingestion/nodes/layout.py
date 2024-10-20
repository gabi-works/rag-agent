import os
import json
import random
import asyncio
import aiohttp

from ingestion.states import FileState
from ingestion.nodes.base import BaseNode
from ingestion.utils.layout_analyzer import LayoutAnalyzeRequester


class LayoutNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__

    def execute(self, state: FileState) -> FileState:
        requester = LayoutAnalyzeRequester(os.environ.get('UPSTAGE_TOKEN'), 
                                           state)
        analysis_request_info = requester.execute_analysis_requests()
        analysis_result_info = requester.excute_analysis_result_requests()

        self.log("LayoutNode execution completed", 
                 total_requests=len(analysis_request_info),
                 sucessed_requests=len([info for info 
                                        in analysis_request_info.values() if info["request_id"]]),
                 succed_get_result_requests=len([info for info 
                                                 in analysis_result_info.values() 
                                                 if info["analyzed_json_file_path"]])
        )
        
        return FileState(analysis_request_info=analysis_request_info)