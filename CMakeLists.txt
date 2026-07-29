cmake_minimum_required(VERSION 3.20)

project(transmission_control_architecture_validation_harness
    VERSION 1.0.0
    LANGUAGES C CXX
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(TCA_WARNINGS_AS_ERRORS "Treat compiler warnings as errors" ON)
option(TCA_ENABLE_SANITIZERS "Enable address and undefined-behavior sanitizers" OFF)
option(TCA_ENABLE_CLANG_TIDY "Run clang-tidy during compilation when available" OFF)

function(tca_enable_quality target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /permissive-)
        if(TCA_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE /WX)
        endif()
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
        if(TCA_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE -Werror)
        endif()
        if(TCA_ENABLE_SANITIZERS)
            target_compile_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
            target_link_options(${target} PRIVATE -fsanitize=address,undefined)
        endif()
    endif()

    if(TCA_ENABLE_CLANG_TIDY)
        find_program(CLANG_TIDY_EXE NAMES clang-tidy REQUIRED)
        set_target_properties(${target} PROPERTIES
            CXX_CLANG_TIDY "${CLANG_TIDY_EXE};--warnings-as-errors=*"
        )
    endif()
endfunction()

add_library(tca_core
    src/can_protocol.cpp
    src/control_application.cpp
    src/plausibility_monitor.cpp
    src/safety_supervisor.cpp
    src/shift_controller.cpp
    src/safety_crc.c
)
target_include_directories(tca_core PUBLIC include)
tca_enable_quality(tca_core)

add_executable(transmission_architecture_runner app/main.cpp)
target_link_libraries(transmission_architecture_runner PRIVATE tca_core)
tca_enable_quality(transmission_architecture_runner)

enable_testing()

add_executable(tca_tests tests/test_main.cpp)
target_link_libraries(tca_tests PRIVATE tca_core)
tca_enable_quality(tca_tests)
add_test(NAME tca_unit_and_integration_tests COMMAND tca_tests)

add_test(NAME architecture_scenario_smoke COMMAND transmission_architecture_runner)
