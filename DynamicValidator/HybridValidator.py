"""
Python script for evaluating the results from dynamic and static validation
"""
import ast
import csv
import os
import re
import sys


"""
Method for evaluating the results of static data flow analysis
path_stat_results - path to the static result files
package_name - identifier of the Android package
provider_list - list of properties of the content provider
"""
def checkstaticresults(path_stat_results, package_name, provider_list):
    static_list = [package_name]
    with open(path_stat_results + package_name + '.apk.txt', 'r') as stat_results_file:
        result_lines = stat_results_file.readlines()
        if len(result_lines) > 0:
            count = 0
            for provider_entry in provider_list:
                if ", " in provider_entry[0]:
                    provider_name = provider_entry[0].split(", ")
                else:
                    provider_name = [provider_entry[0]]
                sources = []
                for provi in provider_name:
                    if "/" in provi:
                        provi = provi.split("L", 1)[1].rsplit(";", 1)[0].replace("/", ".")
                    static_list.append(provi)
                    for i in range(0, len(result_lines)):
                        if provi in result_lines[i] and "return" in result_lines[i]:
                            count = 1
                            i+=1
                            try:
                                while "The sink" not in result_lines[i]:
                                    if "runTaintAnalysis" not in result_lines[i]:
                                        source_method = result_lines[i].split("<", 1)[1].split(">", 1)[0]
                                        if source_method not in sources:
                                            sources.append(source_method)
                                        if "CoPro source - " + result_lines[i] not in static_list:
                                            static_list.append("CoPro source - " + result_lines[i])
                                    i+=1
                            except IndexError:
                                continue
                for source in sources:
                    source_component = source.split(":")[0]
                    if source_component == "android.database.sqlite.SQLiteQueryBuilder":
                        source_component = "android.database.sqlite.SQLiteDatabase"
                    for j in range(0, len(result_lines)):
                        if "<" + source_component in result_lines[j] and "The sink" in result_lines[j]:
                            j+=1
                            try:
                                while "The sink" not in result_lines[j]:
                                    if "runTaintAnalysis" not in result_lines[j]:
                                        source_method = result_lines[j].split("<", 1)[1].split(">", 1)[0]
                                        source_method2 = result_lines[j].rsplit("method <")[1].rsplit(":")[0].replace(".", "/")
                                        if source_method not in sources:
                                            sources.append(source_method)
                                        if re.search(source_method2, str(provider_entry[3])):
                                            if "Source of CoPro source - " + result_lines[j] not in static_list:
                                                static_list.append("Listed source of CoPro source - " + result_lines[j])
                                        else:
                                            if "Source of CoPro source - " + result_lines[j] not in static_list:
                                                static_list.append("Possible source of CoPro source - " + result_lines[j])

                                    j+=1
                            except IndexError:
                                continue
            if count != 0:
                static_list.append(package_name + " - statically validated!")
    return static_list


"""
Method for evaluating the results of dynamic analysis
path_dyn_results - path to the dynamic result files
package_name - identifier of the Android package
provider_list - list of properties of the content provider
"""
def checkdynamicresults(path_dyn_results, package_name, provider_list):
    dynamic_list = [package_name]
    for provider_entry in provider_list:
        provider_authority = provider_entry[1][0]
        if os.path.isfile(path_dyn_results + package_name + " - " + provider_authority):
            dynamic_list.append(provider_authority)
            with open(path_dyn_results + package_name + " - " + provider_authority, 'r') as dyn_results_file:
                result_lines = dyn_results_file.readlines()
                while "\n" in result_lines:
                    result_lines.remove("\n")
                if len(result_lines) > 0:
                    for line in result_lines:
                        dynamic_list.append(line.split("\n")[0])
                    dynamic_list.append(" - dynamically validated!")
    return dynamic_list


"""
Method for initializing the evaluation of the analysis and registering the results 
path_overview - path to the file with the results overview
path_candidates - path to the file for candidate apps
path_static_results - path to the static result files
path_dynamic_results - path to the dynamic result files
path_hybrid - path to the directory for the combined results from static and dynamic analysis 
"""
def validate(path_overview, path_candidates, path_static_results, path_dynamic_results, path_hybrid):
    with open(path_overview, 'w', encoding='utf-8') as over:
        with open(path_candidates, 'r', encoding='utf-8') as csvr:
            reader = csv.reader(csvr)
            dyna_dir_content = [name for name in os.listdir(path_dynamic_results) if os.path.isfile(os.path.join(path_dynamic_results, name))]
            flow_dir_content = [name for name in os.listdir(path_static_results) if os.path.isfile(os.path.join(path_static_results, name))]
            for app in reader:
                package_name = app[0]
                provider_list = ast.literal_eval(app[2])
                with open(path_hybrid + package_name + ".csv", 'w', encoding='utf-8') as csvw2:
                    writer = csv.writer(csvw2)
                    counter = 0
                    if re.search(package_name, str(flow_dir_content)):
                        stat_list = checkstaticresults(path_static_results, package_name, provider_list)
                        writer.writerow(stat_list)
                        if " - statically validated!" in str(stat_list):
                            over.write(package_name + ": static - validated \n")
                            counter += 1
                        else:
                            over.write(package_name + ": static - not validated \n")
                            counter -= 1
                    else:
                        over.write(package_name + ": static - no results \n")
                        counter -= 1
                    if re.search(package_name, str(dyna_dir_content)):
                        dyna_list = checkdynamicresults(path_dynamic_results, package_name, provider_list)
                        writer.writerow(dyna_list)
                        if " - dynamically validated!" in str(dyna_list):
                            over.write(package_name + ": dynamic - validated \n")
                            counter += 1
                        else:
                            over.write(package_name + ": dynamic - not validated \n")
                            counter -= 1
                    else:
                        over.write(package_name + ": dynamic - no results \n")
                        counter -= 1
                    if counter == 2:
                        over.write(package_name + ": hybrid - validated \n")
                    elif counter == -2:
                        over.write(package_name + ": hybrid - not validated \n")
                    writer.writerow(["--","--","--"])
                    over.write("\n")


"""
Method for evaluating the hybrid results labeled with information categories
path_results - path to the directory with the labeled results
path_category_overview - path to the file for the results overview
path_candidates - path to the file for candidate apps
"""
def count(path_results, path_category_overview, path_candidates):
    dir_content = [name for name in os.listdir(path_results) if os.path.isfile(os.path.join(path_results, name))]
    sta_count = [0, 0, 0, 0, 0]
    dyn_count = [0, 0, 0, 0, 0]
    hyb_count = [0, 0, 0, 0, 0]
    count_all = 0
    count_info = 1
    count_conf = 2
    count_appl = 3
    count_pers = 4
    with open(path_category_overview, "w", encoding='utf-8') as out:
        with open(path_candidates, 'r', encoding='utf-8') as csvr:
            reader = csv.reader(csvr)
            for app in reader:
                name = app[0]
                if re.search(name, str(dir_content)):
                    with open(path_results + name + ".csv", 'r', encoding='unicode_escape') as csvr:
                        reader2 = csv.reader(csvr)
                        out.write(name + "\n")
                        for line in reader2:
                            line_str = str(line)
                            if "Stat -" in line_str:
                                sta_count[count_all]+=1
                                if "Info" in line_str:
                                    sta_count[count_info]+=1
                                if "Conf" in line_str:
                                    sta_count[count_conf]+=1
                                if "Appl" in line_str:
                                    sta_count[count_appl]+=1
                                if "Pers" in line_str:
                                    sta_count[count_pers]+=1
                                out.write(line_str + "\n")
                            if "Dyna -" in line_str:
                                dyn_count[count_all] += 1
                                if "Info" in line_str:
                                    dyn_count[count_info] += 1
                                if "Conf" in line_str:
                                    dyn_count[count_conf] += 1
                                if "Appl" in line_str:
                                    dyn_count[count_appl] += 1
                                if "Pers" in line_str:
                                    dyn_count[count_pers] += 1
                                out.write(line_str + "\n")
                            if "Hybr -" in line_str:
                                hyb_count[count_all] += 1
                                if "Info" in line_str:
                                    hyb_count[count_info] += 1
                                if "Conf" in line_str:
                                    hyb_count[count_conf] += 1
                                if "Appl" in line_str:
                                    hyb_count[count_appl] += 1
                                if "Pers" in line_str:
                                    hyb_count[count_pers] += 1
                                out.write(line_str + "\n")
            print(sta_count)
            print(dyn_count)
            print(hyb_count)


"""
Method for analyzing the usage of validated content providers
path_apps_file - path to the file with properties of current Android apps
path_candidates - path to the file for candidate apps
path_usage_result - path for the results file
"""
def checkusage(path_apps_file, path_candidates, path_usage_result):
    csv.field_size_limit(sys.maxsize)
    usage_dict = {}
    with open(path_usage_result, 'w', encoding='utf-8') as erg:
        with open(path_apps_file, 'r', encoding='utf-8') as csvr:
            with open(path_candidates, 'r', encoding='utf-8') as csvr2:
                apps_reader = csv.reader(csvr)
                app_dict = {}
                for app_line in apps_reader:
                    app_dict[app_line[1]] = app_line[2]
                cand_reader = csv.reader(csvr2)
                for cand in cand_reader:
                    perm = ast.literal_eval(cand[1])
                    for p in perm:
                        for app in app_dict.keys():
                            if p in app_dict[app]:
                                if cand[0] not in usage_dict.keys():
                                    usage_dict[cand[0]] = [p + " - " + app]
                                else:
                                    if app[1] not in usage_dict[cand[0]]:
                                        usage_dict[cand[0]].append(p + " - " + app)
                    if cand[0] in usage_dict.keys():
                        erg.write(cand[0] + ": " + str(usage_dict[cand[0]]) + " \n")
                    else:
                        erg.write(cand[0] + ": no usage \n")


if __name__ == '__main__':
    validate("../../Apps/Results/Overview.txt", "../../Apps/Results/Candidate.csv", "../../Apps/Results/Static/", "../../Apps/Results/Dynamic/", "../../Apps/Results/Hybrid/")
    #count("../../Apps/Results/Hybrid_labeled/", "../../Apps/Results/Hybrid_overview.txt" "../../Apps/Results/Candidate.csv")
    #checkusage("../../Apps/appsusage.csv", "../../Apps/Results/Candidate.csv", "../../Apps/Results/Usage.txt")
