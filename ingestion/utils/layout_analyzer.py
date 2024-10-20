import os
import json
import time
import random
import asyncio
import aiohttp
import nest_asyncio
from pathlib import Path
from aiohttp import FormData
from ingestion import logger

UPSTAGE_INFERENCE_URL = "https://ocr-demo.upstage.ai/api/layout-analysis/inference"
UPSTAGE_RESULT_BASE_URL = "https://ocr-demo.upstage.ai/api/result/"

upstage_api_headers = {"Accept": "*/*",
                       "origin": "https://d3tgkvf102zvh7.cloudfront.net",
                       "priority": "u=1, i",
                       "referer": "https://d3tgkvf102zvh7.cloudfront.net/",
                       "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
                       }


class LayoutAnalyzeRequester:
    def __init__(self, token, state):
        self.token = token
        self.file_paths = state["file_paths"]
        self.splitted_file_paths = state["splitted_file_paths"]
        self.analyzed_json_paths = self.file_paths["analyzed_jsons"]
        self.analysis_request_info_path = self.file_paths["analyze_request_info"]

    async def _send_document_analysis_requests(self, target_file_paths):
        analysis_request_info = json.load(open(self.analysis_request_info_path, "r"))
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            tasks = [self._delayed_document_analysis_request(session, fp) 
                     for fp in target_file_paths]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.info(f"Request {idx + 1}: Failed with error {result}", level="error")
                else:
                    if result:
                        file_path = result.get("file_path")
                        request_id = result.get("request_id")
                        logger.info(f"Request {idx + 1} File path[{file_path}]: Request ID = {request_id}")
                        analysis_request_info[file_path]["request_id"] = request_id
            try:
                with open(self.analysis_request_info_path, "w") as f:
                    json.dump(analysis_request_info, f, indent=4)
            except IOError as e:
                logger.info(f"Failed to save request IDs: {e}", level="error")

    async def _delayed_document_analysis_request(self, session, file_path):
        await asyncio.sleep(random.uniform(1, 3))
        return await self._send_document_analysis_request(session, file_path)

    async def _send_document_analysis_request(self, session, file_path):
        request_id = None
        form = FormData()
        form.add_field("token", self.token)
        form.add_field("serviceName", "document-ai")
        form.add_field("type", "drsp")
        form.add_field("url", "receipt-extraction-3.2.0")
        form.add_field("document", open(file_path, 'rb'),
                       filename=file_path,
                       content_type='application/pdf')

        try:
            async with session.post(url=UPSTAGE_INFERENCE_URL, 
                                   headers=upstage_api_headers,
                                   data=form) as response:
                
                if response.status == 200:
                    json_response = await response.json()
                    request_id = json_response.get('requestId')

                else:
                    logger.error(f"[Inference Req Failed]: Status {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"[Inference Req Error]: {e}") 
        
        return {"file_path": file_path, "request_id": request_id}

    async def _send_get_result_requests(self, target_request_info):
        analysis_request_info = json.load(open(self.analysis_request_info_path, "r"))

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            tasks = [self._delayed_get_result_request(session, file_path, info["request_id"])
                     for file_path, info in target_request_info.items()]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Get Result Request {idx + 1}: Failed with error {result}")
                else:
                    file_path = result.get("file_path")
                    result_file_path = result.get("result")
                    analysis_request_info[file_path]["analyzed_json_file_path"] = result_file_path
                    logger.info(f"Get Result Request {idx + 1}: File path {file_path}: Successfully saved result.")
            try:
                with open(self.analysis_request_info_path, "w") as f:
                    json.dump(analysis_request_info, f, indent=4)
            except IOError as e:
                logger.error(f"Failed to save analysis result: {e}")

    async def _delayed_get_result_request(self, session, file_path, request_id):
        await asyncio.sleep(random.uniform(1, 3))
        return await self._send_get_result_request(session, file_path, request_id)

    async def _send_get_result_request(self, session, file_path, request_id):
        result_file_path = os.path.join(self.analyzed_json_paths, Path(file_path).stem + ".json")
        try:
            async with session.get(url=f"{UPSTAGE_RESULT_BASE_URL}/{request_id}",
                                   headers=upstage_api_headers) as response:
                if response.status == 200:
                    with open(result_file_path, "w") as f:
                        json.dump(await response.json(), f, ensure_ascii=False, indent=4)
                        return {"file_path": file_path, "result": result_file_path}
                else:
                    logger.error(f"[Get Result Req Failed]: Status {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"[Get Result Req Error]: {e}")

        return {"file_path": file_path, "result": None}
        
    def execute_analysis_requests(self):
        nest_asyncio.apply()
        sleep_time = 1
        
        while True:
            analysis_request_info = json.load(open(self.analysis_request_info_path, "r"))
            target_file_paths = [file_path 
                                 for file_path, request_info in analysis_request_info.items()
                                 if not request_info["request_id"]]
            
            if (not target_file_paths) or (sleep_time > 64):
                break

            asyncio.run(self._send_document_analysis_requests(target_file_paths))
            sleep_time *= 2
            time.sleep(sleep_time)

        return analysis_request_info
    
    def excute_analysis_result_requests(self):
        nest_asyncio.apply()
        sleep_time = 1

        while True:
            analysis_request_info = json.load(open(self.analysis_request_info_path, "r"))
            target_request_info = {file_path: request_info 
                             for file_path, request_info in analysis_request_info.items() 
                            if not request_info["analyzed_json_file_path"]}

            if (not target_request_info) or (sleep_time > 64):
                break

            asyncio.run(self._send_get_result_requests(target_request_info))
            sleep_time *= 2
            time.sleep(sleep_time)

        return analysis_request_info