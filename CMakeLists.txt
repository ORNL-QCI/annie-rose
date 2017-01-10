cmake_minimum_required(VERSION 2.8)
project(annie-rose)

set(CMAKE_BINARY_DIR ${CMAKE_SOURCE_DIR}/bin)
set(EXECUTABLE_OUTPUT_PATH ${CMAKE_BINARY_DIR})
set(LIBRARY_OUTPUT_PATH ${CMAKE_BINARY_DIR})
set(COMPONENT_PATH ${CMAKE_SOURCE_DIR}/component)
set(COMPONENTS eldispacho armish-fireplace sabot)

foreach(component ${COMPONENTS})
    if(EXISTS ${COMPONENT_PATH}/${component}/)
        add_subdirectory(${COMPONENT_PATH}/${component}/)
    else()
        message(STATUS "${component} missing, skipping build.")
    endif()
endforeach()

# BUG: We have to manually run boot.sh first

# We can't parallelize this build
execute_process(COMMAND uname -r 
    OUTPUT_VARIABLE _output OUTPUT_STRIP_TRAILING_WHITESPACE)
set(flags --with-linux=/lib/modules/${_output}/build CFLAGS=-O3 EXTRA_CFLAGS=-O3)
include(ExternalProject)
ExternalProject_Add(
    openvswitch
    SOURCE_DIR ${COMPONENT_PATH}/ovs/
    BINARY_DIR ${CMAKE_BINARY_DIR}/ovs/
    CONFIGURE_COMMAND "${COMPONENT_PATH}/ovs/configure" ${flags} 
    BUILD_COMMAND make
    INSTALL_COMMAND sudo make install && sudo make modules_install && sudo /sbin/modprobe openvswitch
)