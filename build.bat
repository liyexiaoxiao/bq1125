@echo off
setlocal

rem 带all参数，则执行完整构建，否则执行日常构建
if "%1"=="all" set TT_BUILDALL=1

rem 切换当前目录到构建脚本所在目录
pushd %~dp0

set BUILD_PYTHON=%~dp0Python38-build/python
rem 虚拟环境绝对路径，构建脚本将从此目录中复制第三方库。仅在日常构建中使用。
set TT_VE_PATH=%~dp0ve
rem 嵌入式python运行时的绝对路径，构建脚本将从此目录中复制python运行时。仅在日常构建中使用。
set TT_RT_PATH=%~dp0runtime
rem 源码和构建资源的GIT仓库地址。注意源码必须在主分支，构建资源必须在build分支。仅在完整构建中使用。
set TT_GIT=http://kaleido.iiottt.top/wanHuaTong/kaleido-case-api.git
rem 需要使用cython加密构建的python文件列表，支持glob通配符语法，多个glob项目请用空格分隔
set TT_CYINC=
rem 在以上TT_CYINC包括的文件中，需要排除的文件列表。同样支持多个glob通配符
set TT_CYEXC=Python38-build setup.py *_call.py case0.py expr_core.py case*.py Describe.py 脚本.py *.py
rem 在发布包中需要移除的目录列表，多个目录使用空格分隔，支持*通配符
set TT_CLR_DIRS=.git .vscode __pycache__ build data doc log .idea case run
rem 在发布包中需要移除的文件列表，多个文件使用空格分隔，支持*通配符
set TT_CLR_FILES=.gitignore *.bat requirements.txt demo1.py 1.json .DS_Store 需求图案例.json
rem 指示setup.py删除Cython生成的.c文件和python源文件
set TT_DELETE_SOURCE=1

echo [%time%] 开始构建……

rd /s /q build 2>nul
mkdir build
cd build

if defined TT_BUILDALL (
    echo [%time%] 创建虚拟环境
    python -m venv ve
    rem 这里会修改虚拟环境激活脚本中的代码页，避免其清屏。
    powershell -Command "(gc ve\Scripts\activate.bat) -replace '65001', '936' | Out-File -encoding ASCII ve\Scripts\activate.bat"
    call ve\Scripts\activate.bat

    echo [%time%] Git下载源码
    git clone --single-branch %TT_GIT% fuzz

    echo [%time%] Pip安装第三方模块
    python -m pip install -r fuzz\requirements.txt -i https://pypi.doubanio.com/simple/

    set TT_VE_PATH=ve

    echo [%time%] 下载Python运行时并解压缩
    git clone -b build --single-branch %TT_GIT% res
    powershell Expand-Archive -Force res\runtime.zip fuzz\runtime

) else (
    echo [%time%] 复制源码
    robocopy .. fuzz /mir /xd build /xd %TT_VE_PATH% /xd %TT_RT_PATH% /xd %TT_CLR_DIRS% /xf %TT_CLR_FILES% /nfl /ndl

    echo [%time%] 复制Python运行时
    robocopy %TT_RT_PATH% fuzz\runtime /mir /nfl /ndl
)

echo [%time%] 复制第三方模块到构建目录
robocopy %TT_VE_PATH%\Lib\site-packages fuzz\site-packages /mir /xd __pycache__ pip* setuptools* Cython* /ndl /nfl

cd fuzz

echo [%time%] 使用Cython构建，也即python源码加密
%BUILD_PYTHON% setup.py build_ext --inplace
del setup.py
rmdir /s /q Python38-build

echo [%time%] 清除冗余目录和文件
for /d %%s in (%TT_CLR_DIRS%) do rd %%s /s /q 2>nul
for /d %%s in (%TT_CLR_FILES%) do del %%s /f /q 2>nul

cd ..

if defined TT_BUILDALL (
    echo [%time%] 创建Zip发布包
    powershell Compress-Archive -Path fuzz\* -DestinationPath release.zip
    call ve\Scripts\deactivate.bat
)

:END
echo [%time%] 构建完成！
cd ..
popd
endlocal
