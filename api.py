from omni.services.core import main, routers
import omni.kit.pipapi
import omni.kit.asset_converter as converter

omni.kit.pipapi.install('json')
omni.kit.pipapi.install('asyncio')

from typing import Optional
from pydantic import BaseModel, Field
import json
import asyncio
import os

router = routers.ServiceAPIRouter()

def progress_callback(current_step: int, total: int):
    # Show progress
    print(f"{current_step} of {total}")

class gltfRequestModel(BaseModel):

    """Upload gltf data to Omniverse"""

    input_data: str = Field(
        default = '{"var" : 1}',
        description = " gltf data",
    )

    file_name: str = Field(
        default = "1.gltf",
        description = "gltf file name"
    )

class gltfResponseModel(BaseModel):

    """Return the status of gltf upload"""

    success: bool = Field(
        default = False,
        title = "gltf save status",
        description = "Status of the gltf upload",
    )

    error_message: Optional[str] = Field(
        default = None,
        title = "Error message",
        description = "Optional error message in case the operation was not successful.",
    )

@router.post(
    path=  "/gltf_upload",
    summary = "Upload a gltf model",
    description = "Upload gltf 3D model.",
    response_model = gltfResponseModel,
)

async def upload(request: gltfRequestModel,) -> gltfResponseModel:
    try:
        with open("./test/gltf/" + request.file_name, "w") as gltf_file:
            json.dump(json.loads(request.input_data), gltf_file, indent = 4)
        return gltfResponseModel(
            success = True,
            error_message = None
        )
    except Exception as e:
        return gltfResponseModel(
            success = False,
            error_message = f"{e}"
        )

class ConvertRequestModel(BaseModel):

    """Need Converted gltf file name"""
    
    file_name: str = Field(
        default = "1.gltf",
        description = "gltf file name"
    )

class ConvertResponseModel(BaseModel):

    """Return the status of gltf upload"""

    success: bool = Field(
        default = False,
        title = "gltf convert status",
        description = "Status of the gltf convert result",
    )

    usd_path : str = Field(
        default = "1.usd",
        title = "usd stored path",
        description = "Path of generated usd"
    )

    error_message: Optional[str] = Field(
        default = None,
        title = "Error message",
        description = "Optional error message in case the operation was not successful.",
    )

@router.post(
    path=  "/gltf_convert",
    summary = "Convert a gltf to a usd",
    description = "Convert gltf 3D model into usd format.",
    response_model = ConvertResponseModel,
)

async def convert(request: ConvertRequestModel,) -> ConvertResponseModel:
    task_manager = converter.get_instance()
    file_path = "./test/usd/" + request.file_name.split('.')[0] + '.usd'
    task = task_manager.create_converter_task("./test/gltf/" + request.file_name, file_path, progress_callback)
    OK = await task.wait_until_finished()
    if not OK:
        return ConvertResponseModel(
            success = OK,
            usd_path = None,
            error_message = task.get_error_message()
        )
    return ConvertResponseModel(
        success =  OK,
        usd_path = file_path,
        error_message = None
    )

async def convert(input_asset_path, output_asset_path):
    task_manager = converter.get_instance()
    task = task_manager.create_converter_task(input_asset_path, output_asset_path, progress_callback)
    success = await task.wait_until_finished()
    if not success:
        detailed_status_code = task.get_status()
        detailed_status_error_string = task.get_error_message()

main.register_router(router=router, tags=["gltf convert"],)