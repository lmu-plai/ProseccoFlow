"""
Python script for validating the apps selected as candidates on a real Android device
"""
import ast
import csv
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile
from subprocess import CalledProcessError


"""
Method for dynamically validating Android packages (.apk)
path_candidates - path to the directory of APKs selected as candidates
path_results - path to the directory for dynamic results
permission_list - list of permissions of the content provider
provider_list - list of provider properties (name, authorities, paths)
out3 - path to the file for error messages
"""
def validatecandidates(path_candidates, path_results, package_name, permission_list, provider_list, out3):
    name_attackapp = package_name + '-verify.apk'
    try:
        subprocess.run(['java', '-jar', 'apktool_2.9.3.jar', 'd', 'app-debug.apk'], check=True)
        os.remove('app-debug/AndroidManifest.xml')
        tree = ET.parse('AndroidManifest_orig.xml')
        root = tree.getroot()
        for permission in permission_list:
            new_permission = ET.Element('uses-permission')
            new_permission.set('ns0:name', permission)
            root.append(new_permission)
        ET.indent(tree, '  ')
        tree.write('AndroidManifest.xml', encoding="utf-8", xml_declaration=True)
        os.rename('AndroidManifest.xml', 'app-debug/AndroidManifest.xml')
        subprocess.run(['java', '-jar', 'apktool_2.9.3.jar', 'b', 'app-debug/', '-o', name_attackapp], check=True)
        subprocess.run(['java', '-jar', 'apksigner.jar', 'sign', '--ks', 'keystore.jks', '--ks-pass', 'pass:android', name_attackapp], check=True)
    except CalledProcessError as e1:
        out3.write(package_name + " - " + str(e1) + " - Customization error \n")
    shutil.rmtree('app-debug')
    try:
        subprocess.run(['adb', 'push', path_candidates + package_name + '.apk', '/data/local/tmp/' + package_name + '.apk'], check=True)
        subprocess.run(['adb', 'push', name_attackapp, '/data/local/tmp/' + name_attackapp], check=True)
        subprocess.run(['adb', 'shell', 'pm', 'install', '/data/local/tmp/' + package_name + '.apk'], check=True)
        subprocess.run(['adb', 'shell', 'pm', 'install', '/data/local/tmp/' + name_attackapp], check=True)
    except CalledProcessError as e2:
        out3.write(package_name + " - " + str(e2) + " - Installation error \n")
    time.sleep(3)
    for provider in provider_list:
        provider_authorities = provider[1]
        provider_paths = provider[2]
        count = 1
        path_list = []
        for i in range(0, len(provider_paths)):
            if re.search(r'^/\d*', provider_paths[i]):
                provider_paths[i] = provider_paths[i].split("/")[1]
            path_list.extend(('-e', 'path' + str(count), provider_paths[i]))
            count += 1
        subprocess.run(['adb', 'shell', 'monkey', '-p', package_name, '-v', '100'])
        time.sleep(8)
        for provider_authority in provider_authorities:
            try:
                command = ['adb', 'shell', 'am', 'start', '-a', 'android.intent.action.MAIN', '-n', 'com.proseccoflow.proseccoapp/.MainActivity', '-e', 'authority', provider_authority + '/']
                command.extend(path_list)
                print(command)
                subprocess.run(command, check=True)
            except CalledProcessError as e3:
                out3.write(package_name + " - " + str(e3) + " - Attack error \n")
            time.sleep(5)
            try:
                subprocess.run(['adb', 'pull', '/sdcard/Documents/.' + provider_authority, path_results + package_name + ' - ' + provider_authority], check=True)
            except CalledProcessError as e4:
                out3.write(package_name + " - " + str(e4) + " - Dynamic result error \n")
            subprocess.run(['adb', 'shell', 'am', 'force-stop', 'com.proseccoflow.proseccoapp'])
    subprocess.run(['adb', 'shell', 'pm', 'uninstall', package_name])
    subprocess.run(['adb', 'shell', 'pm', 'uninstall', 'com.proseccoflow.proseccoapp'])
    subprocess.run(['adb', 'shell', 'rm', '/data/local/tmp/' + package_name + '.apk'])
    subprocess.run(['adb', 'shell', 'rm', '/data/local/tmp/' + name_attackapp])
    os.remove(name_attackapp)
    os.remove(name_attackapp + ".idsig")


"""
Method for dynamically validating App bundles (.xapk)
path_candidates - path to the directory of APKs selected as candidates
path_results - path to the directory for dynamic results
permission_list - list of permissions of the content provider
provider_list - list of provider properties (name, authorities, paths)
out3 - path to the file for error messages
"""
def validatesplittedcandidates(path_candidates, path_results, package_name, permission_list, provider_list, out3):
    name_attackapp = package_name + '-verify.apk'
    try:
        subprocess.run(['java', '-jar', 'apktool_2.9.3.jar', 'd', 'app-debug.apk'], check=True)
        os.remove('app-debug/AndroidManifest.xml')
        tree = ET.parse('AndroidManifest_orig.xml')
        root = tree.getroot()
        for permission in permission_list:
            new_permission = ET.Element('uses-permission')
            new_permission.set('ns0:name', permission)
            root.append(new_permission)
        ET.indent(tree, '  ')
        tree.write('AndroidManifest.xml', encoding="utf-8", xml_declaration=True)
        os.rename('AndroidManifest.xml', 'app-debug/AndroidManifest.xml')
        subprocess.run(['java', '-jar', 'apktool_2.9.3.jar', 'b', 'app-debug/', '-o', name_attackapp], check=True)
        subprocess.run(['java', '-jar', 'apksigner.jar', 'sign', '--ks', 'keystore.jks', '--ks-pass', 'pass:android', name_attackapp], check=True)
    except CalledProcessError as e1:
        out3.write(package_name + " - " + str(e1) + " - Customization error \n")
    shutil.rmtree('app-debug')
    with zipfile.ZipFile(path_candidates + package_name + ".xapk", 'r') as zippy:
        zippy.extractall(path_candidates + package_name)
    bundle_content = [name for name in os.listdir(path_candidates + package_name) if os.path.isfile(os.path.join(path_candidates + package_name + "/", name))]
    install_parts = []
    for obj in bundle_content:
        if obj.endswith("apk"):
            install_parts.append(path_candidates + package_name + "/" + obj)
    install_command = ['adb', 'install-multiple']
    install_command.extend(install_parts)
    try:
        subprocess.run(install_command, check=True)
        subprocess.run(['adb', 'push', name_attackapp, '/data/local/tmp/' + name_attackapp], check=True)
        subprocess.run(['adb', 'shell', 'pm', 'install', '/data/local/tmp/' + name_attackapp], check=True)
    except CalledProcessError as e2:
        out3.write(package_name + " - " + str(e2) + " - Installation error \n")
    time.sleep(3)
    for provider in provider_list:
        provider_authorities = provider[1]
        provider_paths = provider[2]
        count = 1
        path_list = []
        for i in range(0, len(provider_paths)):
            if re.search(r'^/\d*', provider_paths[i]):
                provider_paths[i] = provider_paths[i].split("/")[1]
            path_list.extend(('-e', 'path' + str(count), provider_paths[i]))
            count += 1
        subprocess.run(['adb', 'shell', 'monkey', '-p', package_name, '-v', '100'])
        time.sleep(8)
        for provider_authority in provider_authorities:
            try:
                command = ['adb', 'shell', 'am', 'start', '-a', 'android.intent.action.MAIN', '-n', 'com.proseccoflow.proseccoapp/.MainActivity', '-e', 'authority', provider_authority + '/']
                command.extend(path_list)
                print(command)
                subprocess.run(command, check=True)
            except CalledProcessError as e3:
                out3.write(package_name + " - " + str(e3) + " - Attack error \n")
            time.sleep(5)
            try:
                subprocess.run(['adb', 'pull', '/sdcard/Documents/.' + provider_authority, path_results + package_name + ' - ' + provider_authority], check=True)
            except CalledProcessError as e4:
                out3.write(package_name + " - " + str(e4) + " - Dynamic result error \n")
            subprocess.run(['adb', 'shell', 'am', 'force-stop', 'com.proseccoflow.proseccoapp'])
    subprocess.run(['adb', 'shell', 'pm', 'uninstall', package_name])
    subprocess.run(['adb', 'shell', 'pm', 'uninstall', 'com.proseccoflow.proseccoapp'])
    subprocess.run(['adb', 'shell', 'rm', '/data/local/tmp/' + name_attackapp])
    os.remove(name_attackapp)
    os.remove(name_attackapp + ".idsig")


"""
Method for initializing the dynamic validation
path_candidates - path to the directory of APKs selected as candidates
path_results - path to the directory for dynamic result files
out3 - path to the file for error messages
analysis_result - path to the file for candidate apps
"""
def validate(path_candidates, path_results, out3, analysis_result):
    dir_content = [name for name in os.listdir(path_candidates) if os.path.isfile(os.path.join(path_candidates, name))]
    if len(dir_content) != 0:
        for app in analysis_result:
            permission_list = ast.literal_eval(app[1])
            provider_list = ast.literal_eval(app[2])
            for file in dir_content:
                if file.endswith("apk"):
                    package_name = file.split(".apk")[0]
                    if app[0] == package_name:
                        print(package_name)
                        print(permission_list)
                        print(provider_list)
                        validatecandidates(path_candidates, path_results, package_name, permission_list, provider_list, out3)
                elif file.endswith("xapk"):
                    package_name = file.split(".xapk")[0]
                    if app[0] == package_name:
                        print(package_name)
                        print(permission_list)
                        print(provider_list)
                        validatesplittedcandidates(path_candidates, path_results, package_name, permission_list, provider_list, out3)


if __name__ == '__main__':
    with open("Post-candidate.txt", "w", encoding='utf-8') as out3:
        with open("Candidate.csv", 'r', encoding='utf-8') as csvr:
            reader = csv.reader(csvr)
            validate("Cand/", "../../Apps/Results/ProseccoFlow-Results/", out3, reader)
