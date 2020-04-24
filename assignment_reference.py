# 获取URL(高德地图,北京地铁数据):http://map.amap.com/service/subway?_1469083453978&srhdata=1100_drw_beijing.json
import requests
import re
import numpy as np
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

url = 'http://map.amap.com/service/subway?_1469083453978&srhdata=1100_drw_beijing.json'
r = requests.get(url)
# print(r.text) 观察数据结构

# 遍历数据,组成地点数据结构
def get_lines_stations_info(text):
    # 所有线路信息的dict: key:线路名称,value:站点名称list
    lines_info = {}
    # 所有站点信息的dict: key:站点名称,value:站点坐标(x,y)
    stations_info = {}

    pattern = re.compile('"st".*?"kn"')
    lines_list = pattern.findall(text)
    for i in range(len(lines_list)):
        # 地铁线路名
        pattern = re.compile('"ln":".*?"')
        line_name = pattern.findall(lines_list[i])[0][6:-1] # 获取线路名
        # 站点信息list
        pattern = re.compile('"rs".*?"sp"')
        temp_list = pattern.findall(lines_list[i])
        station_name_list = []
        for j in range(len(temp_list)):
            # 地铁站名
            pattern = re.compile('"n":".*?"')
            station_name = pattern.findall(temp_list[j])[0][5:-1] # 获取站名
            station_name_list.append(station_name)
            # 坐标(x,y)
            pattern = re.compile('"sl":".*?"')
            position = pattern.findall(temp_list[j])[0][6:-1] # 获取坐标str
            position = tuple(map(float,position.split(','))) # 转换为float
            # 将数据加入站点信息dict
            stations_info[station_name] = position
        # 将数据加入地铁线路信息dict
        lines_info[line_name] = station_name_list
    return lines_info, stations_info

lines_info ,stations_info = get_lines_stations_info(r.text)
# print(lines_info,'\n',stations_info)
# 建立邻接表
def get_neighbor_info(lines_info):
    # 吧str2加入str1站点的邻接表中
    def add_neighbor_dict(info,str1,str2):
        list1 = info.get(str1)
        if not list1:
            list1 = []
        list1.append(str2)
        info[str1] = list1
        return info
    # 根据线路信息,建立站点邻接表dict
    neighbor_info = {}
    for line_name,station_list in lines_info.items():
        for i in range(len(station_list)-1):
            sta1 = station_list[i]
            sta2 = station_list[i+1]
            neighbor_info = add_neighbor_dict(neighbor_info,sta1,sta2)
            neighbor_info = add_neighbor_dict(neighbor_info,sta2,sta1)
    return neighbor_info

neighbor_info = get_neighbor_info(lines_info)
# print(neighbor_info)

# 画地铁图
plt.figure(figsize=(20,20)) # 设置宽高
stations_graph = nx.Graph()
stations_graph.add_nodes_from(list(stations_info.keys()))
nx.draw(stations_graph,stations_info,with_labels=True,font_size=5, node_size=2)
# plt.show()
stations_connection_graph = nx.Graph(neighbor_info)
nx.draw(stations_connection_graph,stations_info,with_labels=True,font_size=5, node_size=2)
# plt.show()

# 第一种算法:递归查找所有路径
def get_path_DFS_ALL(lines_info, neighbor_info, from_station, to_station):
    """
    递归算法,本质上是深度优先
    遍历所有路径
    这种情况下,站点间的坐标距离难以转化为可靠的启发函数,所以只用简单的BFS算法
    """
    # 检查输入站点名称
    if not neighbor_info.get(from_station):
        print('起始站点{}不存在,请输入正确的站点名称'.format(from_station))
        return None
    if not neighbor_info.get(to_station):
        print('目的站点{}不存在,请输入正确的站点名称'.format(to_station))
        return None
    path = []
    this_station = from_station
    path.append(this_station)
    neighbors = neighbor_info.get(this_station)
    node = {'pre_station':'',
            'this_station':this_station,
            'neighbors':neighbors,
            'path':path}
    return get_next_station_DFS_ALL(node, neighbor_info, to_station)
def get_next_station_DFS_ALL(node, neighbor_info, to_station):
    neighbors = node.get('neighbors')
    pre_station = node.get('this_station')
    path = node.get('path')
    paths = []
    for i in range(len(neighbors)):
        this_station = neighbors[i]
        if (this_station in path):
            # 如果此站点已经在路径中,说明环路,此路不通
            return None
        if neighbors[i] == to_station:
            # 找到终点,返回路径
            path.append(to_station)
            paths.append(path)
            return paths
        else:
            neighbors_ = neighbor_info.get(this_station).copy()
            neighbors_.remove(pre_station)
            path_ = path.copy()
            path_.append(this_station)
            new_node = {'pre_station': pre_station,
                        'this_station': this_station,
                        'neighbors': neighbors_,
                        'path': path_}
            paths_ = get_next_station_DFS_ALL(new_node, neighbor_info, to_station)
            if paths_:
                paths.extend(paths_)

    return paths

paths = get_path_DFS_ALL(lines_info, neighbor_info, '回龙观', '西二旗')
# print('共有{}种路径。'.format(len(paths)))
# for item in paths:
#     print("此路径总计{}站:".format(len(item)-1))
#     print('-'.join(item))

# 第二种算法：没有启发函数的简单宽度优先
def get_path_BFS(lines_info, neighbor_info, from_station, to_station):
    """
    搜索策略：以站点数量为cost（因为车票价格是按站算的）
    这种情况下，站点间的坐标距离难以转化为可靠的启发函数，所以只用简单的BFS算法
    由于每深一层就是cost加1，所以每层的cost都相同，算和不算没区别，所以省略
    """
    # 检查输入站点名称
    if not neighbor_info.get(from_station):
        print('起始站点{}不存在,请输入正确的站点名称'.format(from_station))
        return None
    if not neighbor_info.get(to_station):
        print('目的站点{}不存在,请输入正确的站点名称'.format(to_station))
        return None

    # 搜索节点是个dict，key=站名，value是包含路过的站点list
    nodes = {}
    nodes[from_station] = [from_station]

    while True:
        new_nodes = {}
        for (k, v) in nodes.items():
            neighbor = neighbor_info.get(k).copy()
            if (len(v) >= 2):
                # 不往上一站走
                pre_station = v[-2]
                neighbor.remove(pre_station)
            for station in neighbor:
                # 遍历邻居
                if station in nodes:
                    # 跳过已搜索过的节点
                    continue
                path = v.copy()
                path.append(station)
                new_nodes[station] = path
                if station == to_station:
                    # 找到路径，结束
                    return path
        nodes = new_nodes

    print('未能找到路径')
    return None


# paths = get_path_BFS(lines_info, neighbor_info, '回龙观', '西二旗')
# print("路径总计{}站。".format(len(paths) - 1))
# print("-".join(paths))

# 第三种算法：以路径路程为cost的启发式搜索



def get_path_Astar(lines_info, neighbor_info, stations_info, from_station, to_station):
    """
    搜索策略：以路径的站点间直线距离累加为cost，以当前站点到目标的直线距离为启发函数
    """
    # 检查输入站点名称
    if not neighbor_info.get(from_station):
        print('起始站点{}不存在,请输入正确的站点名称'.format(from_station))
        return None
    if not neighbor_info.get(to_station):
        print('目的站点{}不存在,请输入正确的站点名称'.format(to_station))
        return None

    # 计算所有节点到目标节点的直线距离，备用
    distances = {}
    x, y = stations_info.get(to_station)
    for (k, v) in stations_info.items():
        x0, y0 = stations_info.get(k)
        l = ((x - x0) ** 2 + (y - y0) ** 2) ** 0.5
        distances[k] = l

    # 已搜索过的节点，dict
    # key=站点名称，value是已知的起点到此站点的最小cost
    searched = {}
    searched[from_station] = 0

    # 数据结构为pandas的dataframe
    # index为站点名称
    # g为已走路径，h为启发函数值（当前到目标的直线距离）
    nodes = pd.DataFrame([[[from_station], 0, 0, distances.get(from_station)]],
                         index=[from_station], columns=['path', 'cost', 'g', 'h'])

    count = 0
    while True:
        if count > 1000:
            break
        nodes.sort_values('cost', inplace=True)
        for index, node in nodes.iterrows():
            count += 1
            # 向邻居中离目的地最短的那个站点搜索
            neighbors = neighbor_info.get(index).copy()
            if len(node['path']) >= 2:
                # 不向这个路径的反向去搜索
                neighbors.remove(node['path'][-2])
            for i in range(len(neighbors)):
                count += 1
                neighbor = neighbors[i]
                g = node['g'] + get_distance(stations_info, index, neighbor)
                h = distances[neighbor]
                cost = g + h
                path = node['path'].copy()
                path.append(neighbor)
                if neighbor == to_station:
                    # 找到目标，结束
                    print('共检索%d次。' % count)
                    return path
                if neighbor in searched:
                    if g >= searched[neighbor]:
                        # 说明现在搜索的路径不是最优，忽略
                        continue
                    else:
                        searched[neighbor] = g
                        # 修改此站点对应的node信息
                        #                         nodes.loc[neighbor, 'path'] = path # 这行总是报错
                        #                         nodes.loc[neighbor, 'cost'] = cost
                        #                         nodes.loc[neighbor, 'g'] = g
                        #                         nodes.loc[neighbor, 'h'] = h
                        # 不知道怎么修改df中的list元素，只能删除再新增行
                        nodes.drop(neighbor, axis=0, inplace=True)
                        row = pd.DataFrame([[path, cost, g, h]],
                                           index=[neighbor], columns=['path', 'cost', 'g', 'h'])
                        nodes = nodes.append(row)

                else:
                    searched[neighbor] = g
                    row = pd.DataFrame([[path, cost, g, h]],
                                       index=[neighbor], columns=['path', 'cost', 'g', 'h'])
                    nodes = nodes.append(row)
            # 这个站点的所有邻居都搜索完了，删除这个节点
            nodes.drop(index, axis=0, inplace=True)

        # 外层for循环只跑第一行数据，然后重新sort后再计算
        continue

    print('未能找到路径')
    return None


def get_distance(stations_info, str1, str2):
    x1, y1 = stations_info.get(str1)
    x2, y2 = stations_info.get(str2)
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


paths = get_path_Astar(lines_info, neighbor_info, stations_info, '回龙观', '西二旗')
if paths:
    print("路径总计{}d站。".format(len(paths) - 1))
    print("-".join(paths))