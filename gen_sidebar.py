#coding=utf-8
import os
import os.path
import re
import optparse

indent = "    "

def dump_categories(lines,categories,path,deepth):
    keys = list(categories.keys())
    keys.sort()
    for name in keys:
        if type(categories[name]) is dict:
            count = 0
            for k,v in categories[name].items():
                if type(v) == bool:
                    # file
                    count = count + 1
            lines.append(deepth * indent + "- %s(%s)" % (name,count))
            dump_categories(lines,categories[name], path + "/" + name, deepth+1)
        else:
            lines.append(deepth * indent + "- [%s](%s)" % (name,path + "/" + name + ".md"))


def gen_sidebar(root_path,by_date):
    if not os.path.isdir(root_path):
        print("'%s' not a directory" % root_path)
        return
    date_patten = re.compile("<!--\s*date=(\d+)-(\d+)-(\d+)\s*-->")
    desc_patten = re.compile("<!--\s*(.+)\s*-->")
    categories = {}
    categories_by_date = {}     # date(year-month) -> [day,filename]
    for path,dir_list,file_list in os.walk(root_path):
        current_categories = categories
        relativePath = path.removeprefix(root_path)
        splitpaths = path.split(os.path.sep)
        for i in range(1,len(splitpaths)):
            name = splitpaths[i]
            if not name in current_categories:
                current_categories[name] = {}
            current_categories = current_categories[name]
        for filename in file_list:
            if filename == "index.md" or filename == "README.md":
                continue
            if filename.startswith("_"):
                continue
            if not filename.endswith(".md"):
                continue
            hide = False;
            full_filename = os.path.join(path,filename)
            fp = open(full_filename,"r",encoding="utf-8")
            line = fp.readline()
            matched = date_patten.match(line)
            matched = desc_patten.match(line)
            if matched:
                line = matched.group(1)
                lst = line.split()
                has_date = False
                year,month,day = None,None,None
                for elem in lst:
                    k,v = elem.split("=")
                    if k == "date":
                        has_date = True
                        year,month,day = v.split("-")
                    elif k == "hide":
                        hide = True
                if not hide and by_date and has_date:
                    date = "%04d-%02d" %  (int(year),int(month))
                    if not date in categories_by_date:
                        categories_by_date[date] = []
                    categories_by_date[date].append([day,full_filename.removeprefix(root_path).replace(os.path.sep,"/")])
                fp.close()
            if not hide:
                current_categories[filename.removesuffix(".md")] = True
    lines = []
    dump_categories(lines,categories,"",0)
    def get_day(elem):
        return elem[1]
    if by_date:
        dates = list(categories_by_date.keys())
        dates.sort(reverse=True)
        for date in dates:
            categories_by_date[date].sort(key=get_day)
            lines.append("- %s(%s)" % (date,len(categories_by_date[date])))
            for v in categories_by_date[date]:
                full_filename = v[1]
                basename = os.path.basename(full_filename)
                lines.append(indent + "- [%s](%s)" % (basename.removesuffix(".md"),full_filename))
    data = "\n".join(lines)
    fp = open(os.path.join(root_path,"_sidebar.md"),"w",encoding="utf-8")
    fp.write(data)
    fp.close()

def main():
    usage = "usage: python %prog [options]"
    parser = optparse.OptionParser(usage=usage,version="%prog 0.0.1")
    parser.add_option("-p","--path",help="[optional] article's path",default="docs")
    parser.add_option("-b","--by_date",help="[optional] category by date",type="int",default=1)
    options,args = parser.parse_args()
    path = options.path
    by_date = options.by_date == 1
    gen_sidebar(path,by_date)

if __name__ == "__main__":
    main()
