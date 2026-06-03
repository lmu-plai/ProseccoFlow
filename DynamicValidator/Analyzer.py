"""
Python script for analyzing the AndroidManifest.xml and the code of apps selected as pre-candidates
"""
import csv
import os
import re
import shutil
import time

import apkInspector.axml as ai

from androguard.misc import AnalyzeAPK
from androguard.decompiler.decompile import DvMethod


"""
Method for analyzing the Android manifest for misconfigured parameters of content providers
path_apks - path to the directory of Android packages (APK) to analyze
file - name of the APK 
out2 - path to the file for candidate apps without URI paths from code analysis 
"""
def analyzemanifest(path_apks, file, out2):
    permission_list = []
    provider_list = []
    code_count = 0
    try:
        manifest = ai.parse_apk_for_manifest(path_apks + file)
    except ValueError:
        out2.write(file + " - manifest error \n")
        return
    manifest_lines = manifest.split('\n')
    custom_permissions = []
    content_providers = []
    for line in manifest_lines:
        if "<permission" in line:
            custom_permissions.append(line)
        if "<provider" in line and "android:exported=\"true\"" in line:
            content_providers.append(line)
    if len(content_providers) != 0:
        for provider_line in content_providers:
            provider_name = ""
            provider_authorities = []
            if "ermission=\"" in provider_line:
                provider_line_split = provider_line.split()
                provider_permissions = []
                for element in provider_line_split:
                    if "android:name=\"" in element:
                        provider_name = element.split("\"")[1]
                    if "android:authorities=\"" in element:
                        authority_str = element.split("\"")[1]
                        if ";" in authority_str:
                            authority_list = authority_str.split(";")
                            for auth in authority_list:
                                if auth != '':
                                    provider_authorities.append(auth)
                        else:
                            provider_authorities = [authority_str]
                    if "ermission=\"" in element:
                        provider_permissions.append(element.split("\"")[1])
                pre_perm_list_len = len(permission_list)
                for permission_name in provider_permissions:
                    for permission_line in custom_permissions:
                        if permission_name in permission_line:
                            if "protectionLevel=\"" in permission_line:
                                protection_level = permission_line.split("protectionLevel=\"")[1].split("\"")[0]
                                if protection_level == "0x00000000" and permission_name not in permission_list:
                                    permission_list.append(permission_name)
                            else:
                                if permission_name not in permission_list:
                                    permission_list.append(permission_name)
                post_perm_list_len = len(permission_list)
                if (post_perm_list_len - pre_perm_list_len) != 0:
                    code_count = 1
                    codeanalysis_result = analyzecode(provider_name, provider_authorities, path_apks, file)
                    if codeanalysis_result[2] and codeanalysis_result not in provider_list:
                        provider_list.append(codeanalysis_result)
    if len(provider_list) == 0:
        if code_count == 1:
            out2.write(file + "\n")
        return None
    return [permission_list, provider_list]


"""
Class for nodes of the Abstract Syntax Tree (AST)
"""
class PNode:
    def __init__(self, n, node_id, parent_id):
        self.value = n
        self.node_id = node_id
        self.parent_id = parent_id

    def __repr__(self):
        s = '<PNode %s ID:%s parentID:%s>' \
            % (repr(self.value), self.node_id, self.parent_id)
        return s


"""
Method for processing the AST
n - the AST
"""
def yieldthetree(n, node_id=0, parent_id=0):
    if node_id == 0:
        if not isinstance(n, list):
            yield PNode(n, 0, 0)
            return
        yield PNode(n, 0, 0)
    for i in n:
        node_id += 1
        if isinstance(i, list):
            yield PNode(None, node_id, parent_id)
            for j in yieldthetree(i, node_id, node_id):
                node_id = j.node_id
                yield j
        else:
            yield PNode(i, node_id, parent_id)


"""
Method for the static code analysis to search for provider methods and URI paths 
provider_name_manifest - name of the content provider extracted from the Android manifest
provider_authorities - list with the authorities of the content provider
path_apks - path to the directory of APKs to analyze
file - name of the APK 
"""
def analyzecode(provider_name_manifest, provider_authorities, path_apks, file):
    provider_paths = []
    a, d, dx = AnalyzeAPK(path_apks + file)
    class_list = dx.get_classes()
    name_parts = provider_name_manifest.split(".")
    provider_name_code = ""
    for part in name_parts:
        if provider_name_code == "":
            provider_name_code = part
        else:
            provider_name_code = provider_name_code + "/" + part
    extended_provider_name = ""
    for class_analysis in class_list:
        if provider_name_code in class_analysis.name:
            if class_analysis.extends != "Landroid/content/ContentProvider;" and class_analysis.extends != "Ljava/lang/Object;":
                extended_provider_name = class_analysis.extends
    method_list = []
    for method in dx.get_methods():
        if not method.is_external():
            method_name = method.get_method()
            if provider_name_code in str(method_name) or extended_provider_name != "" and extended_provider_name in str(method_name):
                method_list.append(method)
                for xref in method.get_xref_to():
                    if not xref[1].is_external() and xref[1] not in method_list:
                        method_list.append(xref[1])
    for checked_method in method_list:
        try:
            dv = DvMethod(dx.get_method(checked_method.get_method()))
            dv.process(doAST=True)
            branch = dv.get_ast()
            for key, value in branch.items():
                if key == "body":
                    if "addURI" in str(value) or "appendPath" in str(value) or "Cursor" in str(value) or "equals" in str(value) or "withAppendedPath" in str(value):
                        processed_tree = yieldthetree(value)
                        for node in processed_tree:
                            if "Literal" in str(node):
                                try:
                                    next_node = next(processed_tree)
                                    node_content = str(next_node).split("'")[1]
                                    if re.search('^-?[0-9]*$', node_content) is None and re.search(r'^\s*$', node_content) is None:
                                        if "content://" not in node_content and "Statement" not in node_content and "null" not in node_content and "uri" not in node_content:
                                            if re.search(r'[()#=,!?%&:;]', node_content) is None:
                                                if node_content not in provider_paths:
                                                    provider_paths.append(node_content)
                                except IndexError:
                                    continue
                                except StopIteration:
                                    continue
                    if re.search('[Ss][Ee][Ll][Ee][Cc][Tt]', str(value)):
                        processed_tree = yieldthetree(value)
                        for node in processed_tree:
                            if "Literal" in str(node):
                                try:
                                    next_node = next(processed_tree)
                                    node_content = str(next_node).split("'")[1]
                                    if re.search('^-?[0-9]*$', node_content) is None and re.search(r'^\s*$', node_content) is None:
                                        if "Statement" not in node_content and "null" not in node_content:
                                            if re.search(r'[()#=!?%&:;]', node_content) is None:
                                                select_parts = node_content.split()
                                                for p in range(0, len(select_parts)):
                                                    if re.search('[Ff][Rr][Oo][Mm]', select_parts[p]):
                                                        if select_parts[p + 1] not in provider_paths:
                                                            provider_paths.append(select_parts[p + 1])
                                except IndexError:
                                    continue
                                except StopIteration:
                                    continue
                    if "content://" in str(value):
                        processed_tree = yieldthetree(value)
                        for node in processed_tree:
                            if "Literal" in str(node):
                                try:
                                    next_node = next(processed_tree)
                                    node_content = str(next_node).split("'")[1]
                                    if re.search('^-?[0-9]*$', node_content) is None and re.search(r'^\s*$', node_content) is None:
                                        if "Statement" not in node_content and "null" not in node_content:
                                            if re.search(r'[()#=,!?%&;]', node_content) is None:
                                                uri_path = node_content.split("/", 3)[3]
                                                if uri_path not in provider_paths:
                                                    provider_paths.append(uri_path)
                                except IndexError:
                                    continue
                                except StopIteration:
                                    continue
        except AssertionError:
            continue
    for provider_authority in provider_authorities:
        if provider_authority not in provider_paths:
            if re.search('^@[0-9]*$', provider_authority):
                provider_authorities.remove(provider_authority)
                for path_node in provider_paths:
                    if "." in path_node:
                        provider_authorities.append(path_node)
                        provider_paths.remove(path_node)
        else:
            provider_paths.remove(provider_authority)
    if provider_name_manifest in provider_paths:
        provider_paths.remove(provider_name_manifest)
    if extended_provider_name != "":
        provider_name_result = provider_name_manifest + ", " + extended_provider_name
    else:
        provider_name_result = provider_name_manifest
    result = [provider_name_result, provider_authorities, provider_paths, method_list]
    return result


"""
Method for analyzing the downloaded pre-candidate apps to select candidate apps based on included misconfigurations and URI paths
path_apks - path to the directory of APKs to analyze
path_candidates - path to the directory for APKs selected as candidates
out2 - path to the file for candidate apps without URI paths from code analysis
ares - path to the file for candidate apps with URI paths from code analysis
"""
def analyze(path_apks, path_candidates, out2, ares):
    while True:
        dir_content = [name for name in os.listdir(path_apks) if os.path.isfile(os.path.join(path_apks, name))]
        if len(dir_content) != 0:
            for file in dir_content:
                package_name = file.split(".apk")[0]
                analysis_lists = analyzemanifest(path_apks, file, out2)
                if analysis_lists:
                    writer = csv.writer(ares)
                    permission_list = analysis_lists[0]
                    provider_list = analysis_lists[1]
                    print(permission_list)
                    print(provider_list)
                    writer.writerow([package_name, str(permission_list), str(provider_list)])
                    shutil.move(path_apks + file, path_candidates + file)
                else:
                    os.remove(path_apks + file)
        else:
            time.sleep(3)

if __name__ == '__main__':
    with open("Code-candidate.txt", "w", encoding='utf-8') as out2:
        with open("Candidate.csv", "w", newline='', encoding='utf-8') as ares:
            analyze('APK/', 'Cand/', out2, ares)
