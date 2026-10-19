# 第三方说明

原作《eden》的图片、台词、中文译文、标志和名称不受本项目 MIT 许可覆盖。安装目录的中文补丁不包含可验证的译者署名，文档保留这一不确定性。

PAZ 结构分析参考 morkt 的 GARbro `ArcFormats/Musica/ArcPAZ.cs`，许可为 MIT，完整许可见 `licenses/GARbro-MIT.txt`。Steam《eden》的归档参数参考 Inori/FuckGalEngine 的 `Minori/Minori/fuckpaz/main.cpp` 数据表，未打包该项目的源程序或可执行文件。

Noto Sans Mono CJK SC 的字形子集采用 SIL OFL 1.1，许可见 `licenses/NotoSansCJK-OFL.txt`。Vela 默认系统字体只用于本地字形覆盖分析，没有分发；标题英文按钮在本机栅格化生成，不包含 Windows 字体文件。

转换依赖 Pillow、NumPy、PyCryptodome、fontTools、cryptography；构建及模拟器依赖 Xiaomi aiot-toolkit 与 @aiot-toolkit/emulator。通过各自包管理器安装，源码压缩包不包含这些依赖目录。各依赖仍适用原许可证。
