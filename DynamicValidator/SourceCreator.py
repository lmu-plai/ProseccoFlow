"""
Python script for creating source files for FlowDroid
"""

import xml.etree.ElementTree as ET


"""
Method for combining source files for static data flow analysis with categorized entries
"""
def combinesourceswithcat():
    flowdroid_list = []
    category_dict = {}
    tree = ET.parse("../../IdeaProjects/ProviderFlow/ConditionalSourcesAndSinksAndOthers.xml")
    root = tree.getroot()
    for category in root:
        category_dict[category.get("id")] = category
        for method in category:
            if method[0][0].get("isSource") == "true":
                flowdroid_list.append(method.get("signature"))

    sources_dict = {}
    with open("../../IdeaProjects/ProviderFlow/Ouput_CatSources_v0_9.txt", "r", encoding="utf-8") as SuSiFile:
        susi_sources = SuSiFile.read().splitlines()
        for line in susi_sources:
            line_split = line.split(" (")
            if len(line_split) > 1:
                sources_dict[line_split[0].strip("<>")] = line_split[1].split(")")[0]

    for source in sources_dict.keys():
        if source not in flowdroid_list:
            if sources_dict[source] in category_dict.keys():
                new_method = ET.SubElement(category_dict[sources_dict[source]], 'method', {'signature': source})
            else:
                new_category = ET.SubElement(root,'category', {'id': sources_dict[source]})
                category_dict[sources_dict[source]] = new_category
                new_method = ET.SubElement(new_category, 'method', {'signature': source})
            new_statement = ET.SubElement(new_method, 'return', {'description': "SuSi Sources"})
            ET.SubElement(new_statement, 'accessPath', {'isSource': "true", 'isSink': "false"})
    ET.indent(tree)
    tree.write("SuSi.xml")


"""
Method for combining source files for static data flow analysis without categorized entries
"""
def combinesourceswithoutcat():
    cat = ET.Element
    susi_list = []
    susi_tree = ET.parse("SuSi.xml")
    susi_root = susi_tree.getroot()
    for susi_category in susi_root:
        if susi_category.get('id') == "NO_CATEGORY":
            cat = susi_category
        for susi_method in susi_category:
            if susi_method[0][0].get("isSource") == "true":
                susi_list.append(susi_method.get("signature"))

    sources_list = []
    with open("../../IdeaProjects/ProviderFlow/sources_generated_by_susi_with_android_30.txt", "r", encoding="utf-8") as CoDoCFile:
        codoc_sources = CoDoCFile.read().splitlines()
        for lines in codoc_sources:
            lines_split = lines.split(" ->")
            if len(lines_split) > 1:
                sources_list.append(lines_split[0].strip("<>"))

    for sources in sources_list:
        if sources not in susi_list:
            additional_method = ET.SubElement(cat, 'method', {'signature': sources})
            additional_statement = ET.SubElement(additional_method, 'return', {'description': "CoDoC Sources"})
            ET.SubElement(additional_statement, 'accessPath', {'isSource': "true", 'isSink': "false"})
    ET.indent(susi_tree)
    susi_tree.write("SuSi_CoDoC.xml")


if __name__ == '__main__':
    #combinesourceswithcat()
    combinesourceswithoutcat()
