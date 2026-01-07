import os
import re
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional

from database import User
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/config", tags=["系统配置"])


class ConfigUpdate(BaseModel):
    """配置更新请求"""
    config: Dict[str, Any]


class ConfigResponse(BaseModel):
    """配置响应"""
    config: Dict[str, Any]
    message: str = "success"


def parse_config_file() -> Dict[str, Any]:
    """解析 config.py 文件，提取 Config 类中的变量"""
    config_path = settings.CONFIG_FILE_PATH
    
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="配置文件不存在")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    config_dict = {}
    
    # 定义需要提取的变量及其类型
    config_vars = [
        ("DATA_DIR", "str"),
        ("RUN_TIMES", "int"),
        ("MODE", "str"),
        ("REPLAY_MODE", "str"),
        ("DIR_NAME", "str"),
        ("TEST_PALTFORM_URL", "str"),
        ("SQLALCHEMY_DATABASE_URI", "str"),
        ("DATABASE", "str"),
        ("REPLAY_SOURCE_DATABASE_URI", "str"),
        ("REPLAY_DATABASE_URI", "str"),
        ("REPLAY_START_RUN_ID", "int_or_none"),
        ("REPLAY_END_RUN_ID", "int_or_none"),
        ("READ_INTERVAL", "int"),
        ("SIGNAL_TOLERANCE", "float"),
        ("SINGLE_VARIATION_TIME", "int"),
        ("MULTIPLE_VARIATION_TIME", "int"),
        ("REPEAT_VARIATION_TIME", "int"),
    ]
    
    for var_name, var_type in config_vars:
        # Match patterns like: VAR_NAME = value
        pattern = rf'{var_name}\s*=\s*(.+?)(?:\n|$)'
        match = re.search(pattern, content)
        if match:
            value_str = match.group(1).strip()
            try:
                if var_type == "int":
                    config_dict[var_name] = int(value_str)
                elif var_type == "float":
                    config_dict[var_name] = float(value_str)
                elif var_type == "int_or_none":
                    if value_str == "None":
                        config_dict[var_name] = None
                    else:
                        config_dict[var_name] = int(value_str)
                else:
                    # Remove quotes for strings
                    if value_str.startswith('"') and value_str.endswith('"'):
                        config_dict[var_name] = value_str[1:-1]
                    elif value_str.startswith("'") and value_str.endswith("'"):
                        config_dict[var_name] = value_str[1:-1]
                    elif value_str.startswith("f'") or value_str.startswith('f"'):
                        # f-string, keep as is but mark it
                        config_dict[var_name] = value_str
                    elif "os.path" in value_str or "current_directory" in value_str:
                        # Path expression, keep as is
                        config_dict[var_name] = value_str
                    else:
                        config_dict[var_name] = value_str
            except ValueError:
                config_dict[var_name] = value_str
    
    return config_dict


def write_config_file(config_dict: Dict[str, Any]) -> None:
    """将配置写回 config.py 文件"""
    config_path = settings.CONFIG_FILE_PATH
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for var_name, value in config_dict.items():
        # Build the replacement value
        if value is None:
            value_str = "None"
        elif isinstance(value, str):
            # Check if it's a path expression or f-string
            if "os.path" in value or "current_directory" in value or value.startswith("f"):
                value_str = value
            else:
                value_str = f'"{value}"'
        elif isinstance(value, (int, float)):
            value_str = str(value)
        else:
            value_str = str(value)
        
        # Replace in content - match the variable assignment
        pattern = rf'({var_name}\s*=\s*)(.+?)(\n|$)'
        replacement = rf'\g<1>{value_str}\3'
        content = re.sub(pattern, replacement, content)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)


@router.get("", response_model=ConfigResponse)
async def get_config(current_user: User = Depends(get_current_user)):
    """获取当前系统配置"""
    try:
        config = parse_config_file()
        return ConfigResponse(config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置失败: {str(e)}")


@router.put("", response_model=ConfigResponse)
async def update_config(
    config_update: ConfigUpdate,
    current_user: User = Depends(get_current_user)  # All users can modify
):
    """更新系统配置"""
    try:
        # Get current config
        current_config = parse_config_file()
        
        # Update with new values
        for key, value in config_update.config.items():
            if key in current_config:
                current_config[key] = value
        
        # Write back
        write_config_file(current_config)
        
        return ConfigResponse(config=current_config, message="配置已更新")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post("/upload-replay-db")
async def upload_replay_db(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传 replay.db 文件用于回放模式"""
    if not file.filename.endswith('.db'):
        raise HTTPException(status_code=400, detail="只支持 .db 文件")
    
    # Target path for replay.db in app directory
    target_dir = os.path.join(settings.PROJECT_ROOT, "app")
    os.makedirs(target_dir, exist_ok=True)
    
    target_path = os.path.join(target_dir, "replay.db")
    
    try:
        # Save uploaded file
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "replay.db 上传成功",
            "filename": file.filename,
            "path": target_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")

