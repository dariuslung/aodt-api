from omni.services.core import main, routers
import omni.kit.pipapi
import omni.kit.asset_converter as converter
import omni.usd
from pxr import Usd

omni.kit.pipapi.install('json')
omni.kit.pipapi.install('asyncio')

from typing import Optional
from pydantic import BaseModel, Field
import json
import asyncio
import os

router = routers.ServiceAPIRouter()

# Show progress callback

def progress_callback(current_step: int, total: int):
    # Show progress
    print(f"{current_step} of {total}")


# Upload gltf

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


# Convert gltf to usd

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

async def convert(request: ConvertRequestModel) -> ConvertResponseModel:
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

# Unused, convert template
async def convert(input_asset_path, output_asset_path):
    task_manager = converter.get_instance()
    task = task_manager.create_converter_task(input_asset_path, output_asset_path, progress_callback)
    success = await task.wait_until_finished()
    if not success:
        detailed_status_code = task.get_status()
        detailed_status_error_string = task.get_error_message()


# Test usd

class USDRequestModel(BaseModel):
    
    x: float = Field(
        default = 84,
        description = 'x'
    )

    y: float = Field(
        default = 2,
        description = 'y'
    )

    z: float = Field(
        default = -2610,
        description = 'z'
    )

class USDResponseModel(BaseModel):

    success: bool = Field(
        default = False,
        title = "Status",
        description = "Status",
    )

    new_value : str = Field(
        default = '',
        title = 'New value',
        description = 'New value'
    )

    error_message: Optional[str] = Field(
        default = None,
        title = "Error message",
        description = "Optional error message in case the operation was not successful.",
    )

@router.post(
    path = '/usd',
    summary = "Test usd",
    description = "Test usd",
    response_model = USDResponseModel,
)

async def usd_function(request: USDRequestModel) -> USDResponseModel:
    usd_context = omni.usd.get_context()
    stage_url = 'omniverse://140.113.213.59/Users/aerial/plateau/8F_aodt.usd'
    result, error_str = await usd_context.open_stage_async(stage_url)

    # Gets UsdStage handle
    stage = usd_context.get_stage()
    ru_prim = stage.GetPrimAtPath('/RUs/ru_0001')
    attr = ru_prim.GetAttribute('xformOp:translate')
    attr.Set((request.x, request.y, request.z))
    result, error_str, path = await usd_context.save_stage_async()
    
    return USDResponseModel(
        success = result,
        new_value = str(attr.Get()),
        error_message = error_str
    )

main.register_router(router=router, tags=["gltf convert"],)