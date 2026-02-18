cmake_minimum_required(VERSION 3.22.1)
project("nativecppapp")

# soライブラリ（元々のもの）
add_library(${CMAKE_PROJECT_NAME} SHARED
        native-lib.cpp)

target_link_libraries(${CMAKE_PROJECT_NAME}
        android
        log)

# メモリ負荷テスト用バイナリ
add_executable(mem-check
        mem-check.cpp)
