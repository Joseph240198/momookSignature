// wacom_stu.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>
#include "wgssSTU.h"

int main()
{    
    wgssSTU::IProduct* product = nullptr;
    wgssSTU::IController* controller = nullptr;

    // Inicializar controlador
    if (WGSSSTU_CreateDevice(&controller) != 0) {
        std::cerr << "No se pudo crear el dispositivo" << std::endl;
        return -1;
    }

    if (controller->open() != 0) {
        std::cerr << "No se pudo abrir el STU" << std::endl;
        return -1;
    }

    std::cout << "STU encendido!" << std::endl;

    controller->close();
    controller->release();
    return 0;
    
}

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
