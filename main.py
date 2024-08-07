from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json
from .base import (
    load_config,
    validate_input,
    initialize_twin,
    extract_mesh,
    get_named_selection,
    get_results,
    project_results_on_mesh,
    deflect_mesh,
    export_to_3d_format,
    obtain_maxmin,
    export_output_to_json,
    export_field_to_json
)

app = FastAPI()

@app.post("/load-config")
async def load_config_endpoint():
    try:
        config = await load_config("config.yaml")
        return JSONResponse(content={"status": "Configuration loaded", "config": config})
    except HTTPException as e:
        return JSONResponse(content={"status": "Error", "detail": e.detail}, status_code=e.status_code)

@app.post("/load-data")
async def load_data_endpoint(data: UploadFile = File(...)):
    try:
        config = await load_config("config.yaml")
        data_content = await data.read()
        data = json.loads(data_content)
        await validate_input(data, config)
        return JSONResponse(content={"status": "Data loaded", "data": data})
    except HTTPException as e:
        return JSONResponse(content={"status": "Error", "detail": e.detail}, status_code=e.status_code)

@app.post("/export-3d")
async def export_3d_endpoint(data: UploadFile = File(...)):
    try:
        config = await load_config("config.yaml")
        data_content = await data.read()
        input_data = json.loads(data_content)
        output_format = input_data["output_file"]["3d_file"]["output_format"]
        twin_model, rom_name, twin_outputs = await initialize_twin(input_data, config)
        mesh, grid, mesh_unit = await extract_mesh(input_data)
        scoping_twin, scoping_fea = await get_named_selection(input_data, twin_model, rom_name, mesh)
        result_data, result_unit = await get_results(input_data, config, twin_model, rom_name, scoping_twin)
        result_mesh, result_load_val = await project_results_on_mesh(input_data, result_data, grid)
        deflected_mesh = await deflect_mesh(input_data, config, result_mesh)
        
        await export_to_3d_format(input_data, deflected_mesh)
        return JSONResponse(content={"status": "Result exported to {output_format} format"})
    except HTTPException as e:
        return JSONResponse(content={"status": "Error", "detail": e.detail}, status_code=e.status_code)

@app.post("/export-json")
async def export_json_endpoint(data: UploadFile = File(...)):
    try:
        config = await load_config("config.yaml")
        data_content = await data.read()
        input_data = json.loads(data_content)
        twin_model, rom_name, twin_outputs = await initialize_twin(input_data, config)
        mesh, grid, mesh_unit = await extract_mesh(input_data)
        scoping_twin, scoping_fea = await get_named_selection(input_data, twin_model, rom_name, mesh)
        result_data, result_unit = await get_results(input_data, config, twin_model, rom_name, scoping_twin)
        result_mesh, result_load_val = await project_results_on_mesh(input_data, result_data, grid)
        
        max_min_result = await obtain_maxmin(result_data, "result_detail")
        await export_output_to_json(input_data, result_unit, scoping_twin, twin_outputs, max_min_result)
        return JSONResponse(content={"status": "Results exported to JSON"})
    except HTTPException as e:
        return JSONResponse(content={"status": "Error", "detail": e.detail}, status_code=e.status_code)

@app.post("/export-json")
async def export_json_endpoint(data: UploadFile = File(...)):
    try:
        config = await load_config("config.yaml")
        data_content = await data.read()
        input_data = json.loads(data_content)
        twin_model, rom_name, twin_outputs = await initialize_twin(input_data, config)
        mesh, grid, mesh_unit = await extract_mesh(input_data)
        scoping_twin, scoping_fea = await get_named_selection(input_data, twin_model, rom_name, mesh)
        result_data, result_unit = await get_results(input_data, config, twin_model, rom_name, scoping_twin)
        result_mesh, result_load_val = await project_results_on_mesh(input_data, result_data, grid)

        max_min_result = await obtain_maxmin(result_data, "result_detail")
        await export_field_to_json(input_data, result_unit, scoping_twin, twin_outputs, max_min_result)
        return JSONResponse(content={"status": "Results exported to JSON"})
    except HTTPException as e:
        return JSONResponse(content={"status": "Error", "detail": e.detail}, status_code=e.status_code)


if __name__ == "__main__":
    uvicorn.run(app, host="10.1.20.84", port=8000)