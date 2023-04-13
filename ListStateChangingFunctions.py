#!/usr/bin/env python3
import argparse
import json
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from typing import List, Dict


def parse_args() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to a JSON file to parse for function names")
    args = parser.parse_args()
    return args.file

def getColorVisibility(visibility: str) -> str:
    # visibility: internal private public external
    if visibility == "internal" or visibility == "private":
        return Fore.BLUE
    elif visibility == "public" or visibility == "external":
        return Fore.RED
    else:
        raise Exception("Unknown stateMutability or visibility")

def getColorMutability(stateMutability: str)-> str:
    # mutability: pure view nonpayable payable
    if stateMutability == "pure":
        return Fore.GREEN
    elif stateMutability == "view":
        return Fore.YELLOW
    elif stateMutability == "nonpayable":
        return Fore.MAGENTA
    elif stateMutability == "payable":
        return Fore.LIGHTRED_EX
    else:
        raise Exception("Unknown stateMutability or visibility")

def createPrintableOutput(functionDict: dict, name: str)-> str:
    output = ""
    output += getColorVisibility(functionDict["visibility"])
    output += functionDict["visibility"]
    output += " "
    output += getColorMutability(functionDict["stateMutability"])
    output += functionDict["stateMutability"]
    output += Fore.CYAN
    output += " "
    output += name
    output += Style.RESET_ALL
    output += "("
    paramLen = len(functionDict["parameters"]["parameters"])
    for i in range(0, paramLen):
        param = functionDict["parameters"]["parameters"][i]
        output += param["typeDescriptions"]["typeString"]
        if "name" in param:
            output += " "
            output += param["name"]
        if i != paramLen - 1:
            output += ", "
    output += ")"
    output += Fore.LIGHTYELLOW_EX
    for modifier in functionDict["modifiers"]:
        output += " "
        output += modifier["modifierName"]["name"]
    output += Style.RESET_ALL
    returnParamLen = len(functionDict["returnParameters"]["parameters"])
    if returnParamLen > 0:
        output += " returns("
    for i in range(0, returnParamLen):
        param = functionDict["returnParameters"]["parameters"][i]
        output += param["typeDescriptions"]["typeString"]
        if "name" in param and param["name"] != "":
            output += " "
            output += param["name"]
        if i != returnParamLen - 1:
            output += ", "
    if returnParamLen > 0:
        output += ")"
    return output

def createPrintableOutputParent(parentClass: str, functionDict: dict, name: str)-> str:
    output = ""
    output += Fore.LIGHTGREEN_EX
    output += parentClass
    output += " "
    output += Style.RESET_ALL
    output += createPrintableOutput(functionDict, name)
    return output

def getFunctionNodes(ast: dict, depth: int) -> list:
    ret_list = []
    for astNode in ast["nodes"]:
        if astNode["nodeType"] == "ContractDefinition":
            for baseContract in reversed(astNode["baseContracts"]):
                populateParentFunctions(baseContract["baseName"]["name"], depth)
            for contractNode in astNode["nodes"]:
                if contractNode["nodeType"] == "FunctionDefinition":
                    ret_list.append(contractNode)
    return ret_list

functionsToPrint: Dict[str,str] = dict()

inheritanceTree: List[List[Dict[str,str]]] = []

def populateParentFunctions(parentClass: str, depth: int):
    while len(inheritanceTree) < depth + 1:
        inheritanceTree.append([])
    filePath = "./out/{}.sol/{}.json".format(parentClass, parentClass)
    with open(filePath,"r") as f:
        file_data = json.load(f)
        functionNodes = getFunctionNodes(file_data["ast"], depth+1)
        parentFunctions: Dict[str, str] = dict()
        for node in functionNodes:
            if node["kind"] != "constructor":
                parentFunctions[node["name"]] = createPrintableOutputParent(parentClass, node, node["name"])
        level = inheritanceTree[depth]
        if len(level) == 0:
            inheritanceTree[depth] = [parentFunctions]
        else:
            inheritanceTree[depth].append(parentFunctions)


def findParentFunctionWithSameName(functionName: str) -> bool:
    for i in range(0, len(inheritanceTree)):
        level = inheritanceTree[i]
        for parentClass in level:
            if functionName in parentClass:
                print(parentClass[functionName])
                return True
    return False

if __name__ == "__main__":
    colorama_init()
    f = parse_args()
    with open(f, "r") as abi_file:
        file_data = json.load(abi_file)
        functionNodes = getFunctionNodes(file_data["ast"], 0)
        for node in functionNodes:
            if node["name"] == "" and node["kind"] == "constructor":
                functionsToPrint["constructor"] = createPrintableOutput(node, "constructor")
            else:
                functionsToPrint[node["name"]] = createPrintableOutput(node, node["name"])

        abi = file_data["abi"]
        for function in abi:
            if function["type"] == "function":
                if function["name"] in functionsToPrint:
                    print(functionsToPrint[function["name"]])
                else:
                    success = findParentFunctionWithSameName(function["name"])
                    if(not success):
                        print(Fore.RED + "ERROR" + Style.RESET_ALL + " unknown function source:")
                        print(function["name"])
            