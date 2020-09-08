# 1st part for import information from EGAT excel files (Import_Excel)
# rev2: update yo use with power-query's file of excel which seperate into 4 .xlsx files
# rev3: clean up revison of variable names and comment description
#         there is no vlan setup for host in this version
# perhop version use to create topology from MPLS-tp perhop information 
# this version use to filter node name
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
#--------------------------------------------------------------------- INPUT INFORMATION via Excel power query ----------------------------------------------------------------------#
#####------------- 1) LLinkInfo.xlsx ------ 2) LNodeInfo.xlsx -------- 3) OPGWInfo.xlsx -------- 4) NodeInfo.xlsx -------------- 5) HostInfo.xlsx -----------------#####
# Llink = LogicalLink, Lnode = LogicalNode, LL = LogicalLinkInformation , LN = LogicalNodeInformation
# Olink = OpticalLink, Onode = OpticalNode, OL = OpticalLinkInformation , ON = OpticalNodeInformation, Hinfo = Host Information
Llink = pd.read_excel('D:/EGAT/MasterDegree/07 THESIS Project/02 FullThesis/Resource/Input Data/Testsetup_perhop04/LLinkInfo_perhop.xlsx', sheet_name='LogicalLinkInfo (manual)')
Lnode = pd.read_excel('D:/EGAT/MasterDegree/07 THESIS Project/02 FullThesis/Resource/Input Data/Testsetup_perhop04/LNodeInfo_perhop.xlsx', sheet_name='LogicalNodeInfo')
Olink = pd.read_excel('D:/EGAT/MasterDegree/07 THESIS Project/02 FullThesis/Resource/Input Data/Testsetup_perhop04/OPGWinfo_perhop.xlsx', sheet_name='RawLinkInput') # Use RawInputData of Optical Link 
Onode = pd.read_excel('D:/EGAT/MasterDegree/07 THESIS Project/02 FullThesis/Resource/Input Data/Testsetup_perhop04/NodeInfo_perhop.xlsx', sheet_name='NodeInfo')
Hinfo = pd.read_excel('D:/EGAT/MasterDegree/07 THESIS Project/02 FullThesis/Resource/Input Data/Testsetup_perhop04/HostInfo_perhop.xlsx', sheet_name='HostInput')
# To cleans up and creates only needed data
LN = Lnode[['Node','LogicalNodeName','LLatitude','LLongitude']]
LN = LN.rename(columns={'LogicalNodeName':'Name'})
LL = Llink[['Index','SLNODE','DLNODE','Total Length (km)','Bandwidth (Mbps)','PropagationDelay (ms)']]
LL = LL.rename(columns={'Bandwidth (Mbps)':'BW','PropagationDelay (ms)':'Delay'})
ON = Onode[['NODE','Latitude','Longitude']]
ON = ON.rename(columns={'NODE':'Name'})
OL = Olink[['Source','Destination','Length']]
HI = Hinfo[['HostName','LogicalNodeName','Latitude','Longitude','Bandwidth (Mbps)']]
HI = HI.rename(columns={'HostName':'Name','Bandwidth (Mbps)':'Bandwidth'})
#HOST data use for creation of .JSON
HpositionDict = pd.Series(HI.LogicalNodeName.values,index=HI.Name).to_dict() # Store LNname that connect to each host as a dict (key=hostname ('station'), value=LNname ('PL2_1'))
HLatDict = pd.Series(HI.Latitude.values,index=HI.LogicalNodeName).to_dict() # Store Latitude of each host as a dict (key=LNname ('PL2_1'), value = HLatitude)
HLongDict = pd.Series(HI.Longitude.values,index=HI.LogicalNodeName).to_dict() # Store Longitude of each host as a dict (key=LNname ('PL2_1'), value = HLongitude)
#######---------------------------------------------------- Python script data Manipulation -----------------------------------------------------########
################## Read original .py to copy the lines #################
#------------------------ This version use with VPLS_orig.py ----------------------------#
#--------------------->>> new_py.writelines( rline[0:42] ) -----------------------------------#
#----------------------------new_py.writelines( rline[44:]) <<<<-----------------------------#
path = 'C:/Users/Saranj/Documents/Python Scripts/THESIS_ImportExcel/VPLS_orig.py'
with open(path, 'r') as reader:
    # readlines creates a list of th lines
    rline = reader.readlines()
################## Open new file to write the lines to #######################
new_path = 'C:/Users/Saranj/Documents/Python Scripts/THESIS_ImportExcel/EGAT_VPLS_perhop04rev1.py'
new_py = open(new_path,'w')
##################################>>>>>>>>>    Global Utility   <<<<<<<<<<###################################
#---------------------------------------------------- abbreviation -----------------------------------------------------#
hostLineList = [] # use to store list of 'coding line' for creation of every host 
switchLineList = []  # use to store list of 'coding line' for creation of every Logical Switches (LN)
HSLineList = [] # use to store list of 'coding line' for creation of Host-Switch Link
LinkLineList = [] # use to store list of 'coding line' for creation of Switch-Switch Link
#---------------------------------------- Dictionary for global data ----------------------------------------------#
LNportDict = {} # Dictionary for number of usage ports in each Logical Node (key=LNname, value = number of usage )
HDict = {} # Dictionary for hostname (key = 'hostname', value = 'h..' )
LNDict = {} # Dictionary for Logical Node (key = 'LogicalNodeName', value = 's..')
#------------------------------ Function use to count the number usage in LN ---------------------------#
# data = LNportDict, key = LogicalNodeName ie. 'PL2_1'
def update_LNport(data,key):
    if key in LNportDict: # if there is already a 'key' in LNportDict, increase that number usage by 1
        data[key] += 1
    else: # if there is no 'key', create that key and set number of use equal to 1
        data[key] = 1
############################################# End of Global Utility #############################################

#####################>>>>>>>>>>>>>>>>>>  Writing Part <<<<<<<<<<<<<<<<<<##########################
#--------------------------- Paste first half of lines from original path ---------------------------------------#
new_py.writelines( rline[0:42] )
#-------------------------------- Add lines to insert between original lines ---------------------------------#
####################### Create Host from host information #####################
hostnameList = HI['Name'].tolist() # List of hosts <this information will also be use in H-S creation part>
hostBWList = HI['Bandwidth'].tolist() # this information will also be use in H-S creation part
# Since we imports information from input excel that has 'null' we have to clear our lists from NaN
hostnameList = [x for x in hostnameList  if str(x) != 'nan']
hostBWList = [x for x in hostBWList  if str(x) != 'nan']
hostMACDict = {} # Dictionary use to store MAC of each host {'h1': '00:00:00:00:00:01', 'h2': '00:00:00:00:00:02'}
for i in range(0,len(hostnameList)):
        HDict[hostnameList[i]] = 'h%d' % (i+1) # To name 'h1' .... according to 'hostname'
        # NOTE: in mininet host must consist of number ie. 'PL2', 'PL1', so better fill the name with 'h..' instead of hostname
        hostLineList.append("        %s = self.addHost('%s', mac='00:00:00:00:00:%02d') #%s \n" % (HDict[hostnameList[i]], HDict[hostnameList[i]],i+1,hostnameList[i])) 
        hostMACDict[HDict[hostnameList[i]]] = '00:00:00:00:00:%02d'%(i+1)
#*************** Write information into Python-file *****************#
new_py.writelines(hostLineList)
new_py.write('\n')
######################### End of Host creation  #############################
###################### Create Swtich from LN information #####################
LNnameList = LN['Name'].tolist() # List of LogicalNode name
LNLat = LN['LLatitude'].tolist() # List of LogicalNode's 'Latitude
LNLong = LN['LLongitude'].tolist() # List of LigicalNode's Longitude
dpidDict = {} # Dictionary use to store dpid of each switch {'s1' : 0000ffffffff0001, 's2': 0000ffffffff0002}
for i in range(0,len(LNnameList)):
    # NOTE: in s1 = self.addSwitch('s1'), 's1' must always setting to 's...' or the mininet will not works
    LNDict[LNnameList[i]] = 's%d' % (i+1) # To name 's1' .... according to 'LNname'
    switchLineList.append("        %s = self.addSwitch('%s', dpid='0000ffffffff0%03d', annotations={'latitude': '%s', 'longitdue': '%s'}) #%s \n" %(LNDict[LNnameList[i]], LNDict[LNnameList[i]],i+1,LNLat[i],LNLong[i],LNnameList[i]))
    dpidDict["%s"%(LNnameList[i])] = '0000ffffffff0%03d'%(i+1)
#*************** Write information into python-file ******************#
new_py.writelines(switchLineList)
new_py.write('\n')
######################### End of Switch creation ############################
############################ Create HOST-SW link ##########################
# Number of Host-Swich link must equal to number of host so we create host-switch link according to HostInfo
for i in range(0,len(hostnameList)):
    update_LNport(LNportDict,'%s' % (HpositionDict[hostnameList[i]])) # HOSTpostionDict[hostnameList[i]] = LogicalNodeName for each host ie. 'PL2_1'
    portnum = LNportDict['%s'%(HpositionDict[hostnameList[i]])] # update port number that was used according to each host
    # Note: port1 = LN  port as remember from LNportDict, port2 = Host port which equal to 0
    # Note2: LNDict[HpositionDict[hostnameList[i]]] use to convert from host name ie. 'PL2' to LogicalNodeName for that host ie. 'PL2_1' then convert to LNDict such as 's16'
    # Note3: reduce TClink between host and switch
    HSLineList.append("        self.addLink(%s, %s, port1=%d, port2=0)\n" % (LNDict[HpositionDict[hostnameList[i]]], HDict[hostnameList[i]], portnum))
#     HSLineList.append("        self.addLink(%s, %s, cls=TCLink, port1=%d, port2=0, bw=%d)\n" % (LNDict[HpositionDict[hostnameList[i]]], HDict[hostnameList[i]], portnum,hostBWList[i]))
#**************** Write information into python-file ******************#
new_py.writelines(HSLineList)
new_py.write('\n')
######################## End of HOST-SW creation #######################
##########################  Create Logical Link  #########################
LLindex = LL['Index'].tolist()
LLsource = LL['SLNODE'].tolist()
LLdest = LL['DLNODE'].tolist()
LLBW = LL['BW'].tolist()
LLdelay = LL['Delay'].tolist()
for i in range(0,len(LLindex)):
    # Update both 'source' and 'destination' usage port
    # Source update
    update_LNport(LNportDict,'%s' % (LLsource[i])) # Update from source name
    portnum_s = LNportDict['%s'%(LLsource[i])]
    # Destination update
    update_LNport(LNportDict,'%s' % (LLdest[i])) # Update from destination name
    portnum_d = LNportDict['%s'%(LLdest[i])]
    LinkLineList.append("        self.addLink(%s, %s, cls=TCLink, port1=%d, port2=%d, bw=%d, delay='%fms')\n" % (LNDict[LLsource[i]], LNDict[LLdest[i]], portnum_s, portnum_d, LLBW[i], LLdelay[i]))
#*************** Write information into python-file ***************#
new_py.writelines(LinkLineList)
new_py.write('\n')
###################### End of Logical Link creation #####################
#------------------------- Paste the rest of line afther insert ---------------------------#
new_py.writelines( rline[44:])
#########################>>>>>>>>>>>  End of Writing part <<<<<<<<<<<<<###########################
# Close original and the new one
reader.close()
new_py.close()
#######------------------------------------------------ End of Python script data Manipulation -------------------------------------------------########
###-------------------- to create network-configuration.json -----------------------###
# note: with json.dump we can create json file with {} according to dict and [] according to List
import json # use too convert data to .json
dict_data = {}
dict_data["devices"] = {}
dict_data['hosts'] = {}
dict_data['ports'] = {}
dict_data['apps'] = {}
dpidHostDict = {} # Dict for 'dpid/port' that connect to HOST (ex of:0000ffff00xx/1)
#/////////-------------------------- devices & dpid information ------------------------------/////#
if len(dpidDict) > 0 :
    for i in range(0, len(dpidDict)):
        dict_data["devices"]["of:"+dpidDict[LNnameList[i]]] = {}
        dict_dpid_basic = {}
        dict_dpid_basic["basic"] = {}
        dict_dpid_basic["basic"]["name"] = LNnameList[i]
        dict_dpid_basic['basic']['latitude'] = LNLat[i]
        dict_dpid_basic['basic']['longitude'] = LNLong[i]
        dict_data['devices']['of:'+dpidDict[LNnameList[i]]] = dict_dpid_basic
#/////////-------------------------- hosts information ------------------------------/////#
if len(hostMACDict) > 0:
    for i in range (0,len(hostMACDict)) :
        counter_MAC = hostMACDict[HDict[hostnameList[i]]] + "/-1" # this counter use to create string of MAC/-1 of each hosts
        portHostString = 'of:'+dpidDict[HpositionDict[hostnameList[i]]]+"/1"
        dpidHostDict[hostnameList[i]] = portHostString #matching Host with Switch port dictionary
        dict_data['hosts'][counter_MAC] = {} # this version for no VLAN at host
        dict_data['hosts'][counter_MAC]['basic'] = {}
        dict_data['hosts'][counter_MAC]['basic']['locations'] = ['of:'+dpidDict[HpositionDict[hostnameList[i]]]+"/1"] #  to create of:0000ffffffff00xx according to switch that connect with host
        dict_data['hosts'][counter_MAC]['basic']['ips'] = ["10.0.0.%d"%(i+1)]
        dict_data['hosts'][counter_MAC]['basic']['name'] = HDict[hostnameList[i]] # to put info of h1 .. instead of host's name
        dict_data['hosts'][counter_MAC]['basic']['latitude'] = HLatDict[HpositionDict[hostnameList[i]]]
        dict_data['hosts'][counter_MAC]['basic']['longitude'] = HLongDict[HpositionDict[hostnameList[i]]]
#/////////---------------------------------------- interfaces information ------------------------------------/////#
if len(dpidHostDict) > 0:
    for i in range (0,len(dpidHostDict)) :
        dict_data['ports'][dpidHostDict[hostnameList[i]]] = {}
        dict_data['ports'][dpidHostDict[hostnameList[i]]]['interfaces'] = [] # to create 'interfaces' with list type (to show as [] not {}) we must create dictionary inside 'interfaces's list'
        name_dict = {}
        name_dict['name'] = HDict[hostnameList[i]] # to put info of h1 .. instead of host's name
        dict_data['ports'][dpidHostDict[hostnameList[i]]]['interfaces'].append(name_dict) # append this name_dict (unname in .json) to list of 'interfaces
#/////////-------------------------------------- application information ----------------------------------------/////#
# perhop_rev will clear all VPLS since there are so many bug in application
# for this version we have only one VPLS group 
# VPLSgroupList = []
# VPLSgroupList.append('VPLS1') # only one VPLS group
# dict_data['apps']['org.onosproject.vpls'] = {}
# dict_data['apps']['org.onosproject.vpls']['vpls'] = {}
# if len(VPLSgroupList) > 0:   # check from number of HOST
#     # use to calculate the list of host (h_list)
#     h_list = []
#     for i in range(0,len(hostnameList)):
#         h_list.append(HDict[hostnameList[i]])
#     for i in range (0, len(VPLSgroupList)):
#         dict_data['apps']['org.onosproject.vpls']['vpls']['vplsList'] = [] # create vplsList as a list instead of dict 
#         vplsList_dict = {}
#         vplsList_dict['name'] = VPLSgroupList[i]
# #         vplsList_dict['interfaces'] = HDict[hostnameList] # Add every host to this group / need to fix in other version
#         vplsList_dict['interfaces'] = h_list # use host dict as a list ie. [ 'h1', 'h2']
#         vplsList_dict['encapsulation'] = 'vlan' # Option in VPLS application 
# #         dict_data['apps']['org.onosproject.vpls']['vpls']['vplsList']['name'] = VPLSgroupList[i]
# #         dict_data['apps']['org.onosproject.vpls']['vpls']['vplsList']['interfaces'] = hostnameList 
# #         dict_data['apps']['org.onosproject.vpls']['vpls']['vplsList']['encapsulation'] = 'vlan' 
#         dict_data['apps']['org.onosproject.vpls']['vpls']['vplsList'].append(vplsList_dict) # append vplsList_dict (unname in .json) to list of 'vpls'
# to convert all information to json
with open('EGAT_VPLS_perhop04rev1.json', "w") as js:
    json.dump(dict_data,js)
