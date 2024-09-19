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
STAGE_URL = 'omniverse://140.113.213.59/Users/aerial/plateau/8F_aodt.usd'

# Show progress callback

def progress_callback(current_step: int, total: int):
    # Show progress
    print(f"{current_step} of {total}")


# Upload gltf

class gltfRequest(BaseModel):

    """Upload gltf data to Omniverse"""

    input_data: str = Field(
        default = '{"var" : 1}',
        description = " gltf data",
    )

    file_name: str = Field(
        default = "1.gltf",
        description = "gltf file name"
    )

class gltfResponse(BaseModel):

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
    tags = ['glTF'],
    response_model = gltfResponse,
)

async def upload(request: gltfRequest) -> gltfResponse:
    try:
        with open("./test/gltf/" + request.file_name, "w") as gltf_file:
            json.dump(json.loads(request.input_data), gltf_file, indent = 4)
        return gltfResponse(
            success = True,
            error_message = None
        )
    except Exception as e:
        return gltfResponse(
            success = False,
            error_message = f"{e}"
        )


# Convert gltf to usd

class ConvertRequest(BaseModel):

    """Need Converted gltf file name"""
    
    file_name: str = Field(
        default = "1.gltf",
        description = "gltf file name"
    )

class ConvertResponse(BaseModel):

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
    tags = ['glTF'],
    response_model = ConvertResponse,
)

async def convert(request: ConvertRequest) -> ConvertResponse:
    task_manager = converter.get_instance()
    file_path = "./test/usd/" + request.file_name.split('.')[0] + '.usd'
    task = task_manager.create_converter_task("./test/gltf/" + request.file_name, file_path, progress_callback)
    OK = await task.wait_until_finished()
    if not OK:
        return ConvertResponse(
            success = OK,
            usd_path = None,
            error_message = task.get_error_message()
        )
    return ConvertResponse(
        success =  OK,
        usd_path = file_path,
        error_message = None
    )

# Unused, convert template
# async def convert(input_asset_path, output_asset_path):
#     task_manager = converter.get_instance()
#     task = task_manager.create_converter_task(input_asset_path, output_asset_path, progress_callback)
#     success = await task.wait_until_finished()
#     if not success:
#         detailed_status_code = task.get_status()
#         detailed_status_error_string = task.get_error_message()

# RU Get

class RUGetAttrRequest(BaseModel):

    prim_name: str = Field(
        default = 'ru_0001',
        description = 'Primitive name'
    )

class RUGetAttrResponse(BaseModel):

    success: bool = Field(
        default = False,
        title = "Status",
        description = "Status",
    )

    value : str = Field(
        default = '',
        title = 'Get value',
        description = 'Get value'
    )

    error_message: Optional[str] = Field(
        default = None,
        title = "Error message",
        description = "Optional error message in case the operation was not successful.",
    )

@router.post(
    path = '/ru_get_attr',
    summary = "RU get attribute",
    description = "RU get attribute",
    tags = ['RU'],
    response_model = RUGetAttrResponse
)

async def usd_function(request: RUGetAttrRequest) -> RUGetAttrResponse:
    usd_context = omni.usd.get_context()
    result, error_str = await usd_context.open_stage_async(STAGE_URL)

    # Gets UsdStage handle
    stage = usd_context.get_stage()
    path = '/RUs/'
    path += request.prim_name
    prim = stage.GetPrimAtPath(path)
    if not prim:
        return RUGetAttrResponse(
            success = False,
            error_message = 'Specified prim does not exist'
        )
    attr = prim.GetAttribute('xformOp:translate')
    times = attr.GetTimeSamples()

    # For UE attribute with TimeCode
    if times:
        get_value = attr.Get(times[0])
    	
    # For RU static attribute
    else:
        get_value = attr.Get()
    
    return RUGetAttrResponse(
        success = result,
        value = str(get_value),
        error_message = error_str
    )


# RU Set

class RUSetAttrRequest(BaseModel):

    prim_name: str = Field(
        default = 'ru_0001',
        description = 'Primitive name'
    )

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

class RUSetAttrResponse(BaseModel):

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
    path = '/ru_set_attr',
    summary = "RU set attribute",
    description = "RU set attribute",
    tags = ['RU'],
    response_model = RUSetAttrResponse
)

async def usd_function(request: RUSetAttrRequest) -> RUSetAttrResponse:
    usd_context = omni.usd.get_context()
    stage_url = 'omniverse://140.113.213.59/Users/aerial/plateau/8F_aodt.usd'
    result, error_str = await usd_context.open_stage_async(stage_url)

    # Gets UsdStage handle
    stage = usd_context.get_stage()
    path = '/RUs/'
    path += request.prim_name
    prim = stage.GetPrimAtPath(path)
    if not prim:
        return RUSetAttrResponse(
            success = False,
            error_message = 'Specified prim does not exist'
        )
    attr = prim.GetAttribute('xformOp:translate')
    times = attr.GetTimeSamples()
    
    # For UE attribute with TimeCode
    if times:
        attr.Set((request.x, request.y, request.z), times[0])
        new_value = attr.Get(times[0])
    	
    # For RU static attribute
    else:
        attr.Set((request.x, request.y, request.z))
        new_value = attr.Get()

    # Save stage
    result, error_str, path = await usd_context.save_stage_async()
    
    return RUSetAttrResponse(
        success = result,
        new_value = str(new_value),
        error_message = error_str
    )


# UE Get

class UEGetAttrRequest(BaseModel):

    prim_name: str = Field(
        default = 'ue_0001',
        description = 'Primitive name'
    )

class UEGetAttrResponse(BaseModel):

    success: bool = Field(
        default = False,
        title = "Status",
        description = "Status",
    )

    value : str = Field(
        default = '',
        title = 'Get value',
        description = 'Get value'
    )

    error_message: Optional[str] = Field(
        default = None,
        title = "Error message",
        description = "Optional error message in case the operation was not successful.",
    )

@router.post(
    path = '/ue_get_attr',
    summary = "UE get attribute",
    description = "UE get attribute",
    tags = ['UE'],
    response_model = UEGetAttrResponse
)

async def usd_function(request: UEGetAttrRequest) -> UEGetAttrResponse:
    usd_context = omni.usd.get_context()
    result, error_str = await usd_context.open_stage_async(STAGE_URL)

    # Gets UsdStage handle
    stage = usd_context.get_stage()
    path = '/UEs/'
    path += request.prim_name
    prim = stage.GetPrimAtPath(path)
    if not prim:
        return UEGetAttrResponse(
            success = False,
            error_message = 'Specified prim does not exist'
        )
    attr = prim.GetAttribute('xformOp:translate')
    times = attr.GetTimeSamples()

    # For UE attribute with TimeCode
    if times:
        get_value = attr.Get(times[0])
    	
    # For RU static attribute
    else:
        get_value = attr.Get()
    
    return UEGetAttrResponse(
        success = result,
        value = str(get_value),
        error_message = error_str
    )


# RU Set

class UESetAttrRequest(BaseModel):

    prim_name: str = Field(
        default = 'ue_0001',
        description = 'Primitive name'
    )

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

class UESetAttrResponse(BaseModel):

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
    path = '/ue_set_attr',
    summary = "UE set attribute",
    description = "UE set attribute",
    response_model = UESetAttrResponse,
    tags = ['UE']
)

async def usd_function(request: UESetAttrRequest) -> UESetAttrResponse:
    usd_context = omni.usd.get_context()
    stage_url = 'omniverse://140.113.213.59/Users/aerial/plateau/8F_aodt.usd'
    result, error_str = await usd_context.open_stage_async(stage_url)

    # Gets UsdStage handle
    stage = usd_context.get_stage()
    path = '/UEs/'
    path += request.prim_name
    prim = stage.GetPrimAtPath(path)
    if not prim:
        return UESetAttrResponse(
            success = False,
            error_message = 'Specified prim does not exist'
        )
    attr = prim.GetAttribute('xformOp:translate')
    times = attr.GetTimeSamples()
    
    # For UE attribute with TimeCode
    if times:
        attr.Set((request.x, request.y, request.z), times[0])
        new_value = attr.Get(times[0])
    	
    # For RU static attribute
    else:
        attr.Set((request.x, request.y, request.z))
        new_value = attr.Get()

    # Save stage
    result, error_str, path = await usd_context.save_stage_async()
    
    return UESetAttrResponse(
        success = result,
        new_value = str(new_value),
        error_message = error_str
    )

main.register_router(router=router)
