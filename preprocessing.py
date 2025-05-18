import numpy as np
import pandas as pd
#%%
def optimTh(data_array):
    
    i = 0
    while i<len(data_array):
        tmets = data_array[i]
        i += 1
        if tmets != 0:
            break
    i = i - 1
    j = 1439 
    while j>=0:
        tmets = data_array[j]
        j -= 1    
        if tmets != 0:
            break
    j = j + 1

    # 全部0の場合
    if i == 1439 and j == 0:
        return 1.0

    trackingdata = data_array[i:j]
    zeronum = len(trackingdata)-np.count_nonzero(trackingdata)
    active = np.where(trackingdata > 1.5)
    numsed = len(trackingdata) -  len(active)
    # numsedが0の場合
    if numsed == 0:
        return 1.0
    zeroRatio_original = zeronum/numsed
    coef = -0.669  #回帰係数
    intercept = 0.684 #切片(誤差)
    
    optim_thlethold = coef*zeroRatio_original+intercept
    
    return optim_thlethold
    
#%%
def zeroProb(data_array,define_range,ratio,visualize):
    judge_1 = np.zeros((1440,1440))
    judge_2 = np.zeros((1440,1440))
    judge_1[:,:] = np.nan
    judge_2[:,:] = np.nan
    i = 0
    while i<len(data_array): 
    #breakまで無限ループの繰り返し
        tmets = data_array[i]
        #print(i)
        i += 1  # i = i+ 1 に同じ
        if tmets != 0: # tmets が0と異なる場合
            break
        #ここで記録される[i]は最初に[0]以外の数字が出てくるフレーム数
    i = i - 1
    
    j = 1439 
    while j>=0:
        tmets = data_array[j]
        #print(j)
        j -= 1    
        if tmets != 0:
            break
        #ここで記録される[j]は最後に[0]以外の数字が出てくるフレーム数
    j = j + 1

    # 全部0の場合
    if i == 1439 and j == 0:
        return np.zeros(1440)
    
    for a in range(i,j+1):        
        
        if a > j-define_range:
            if a == j:
                hourdata = data_array[a]
                nonzeronum = np.count_nonzero(hourdata)
                xx = 1.0
                judge_1[a,a] = xx
            else:
                hourdata = data_array[a:j+1]
                nonzeronum = np.count_nonzero(hourdata)
                xx = nonzeronum/len(hourdata)
                judge_1[a,a:j+1] = xx
              
        else:
            hourdata = data_array[a:a+define_range]
            nonzeronum = np.count_nonzero(hourdata)
            xx = nonzeronum/len(hourdata)
            judge_1[a,a:a+(define_range)] = xx
             
    for a in reversed(range(i,j+1)):     
        if a - define_range < i:
            if a == i:
                hourdata = data_array[a:a+1]
                nonzeronum = np.count_nonzero(hourdata)
                xx = 1.0
                judge_2[a,a] = xx
            else:
                hourdata = data_array[i:a+1]
                nonzeronum = np.count_nonzero(hourdata)
                xx = nonzeronum/len(hourdata)
                judge_2[a,i:a+1] = xx
        else:
            hourdata = data_array[a+1-define_range:a+1]
            nonzeronum = np.count_nonzero(hourdata)
            xx = nonzeronum/len(hourdata)
            judge_2[a,a+1-define_range:a+1] = xx
        # print(a, len(hourdata), xx)
        # print(a, xx)
            
    
    out1 = np.zeros((1440,1))
    out2 = np.zeros((1440,1))
    r_wear = np.zeros((1440,1))
    corrected_prob = []
    init_zeros = np.zeros(i)
    corrected_prob = np.append(corrected_prob,init_zeros)

    for a in range(i,j+1):
        eachtime1 = judge_1[:,a]
        mean_judge1 = np.nanmean(eachtime1)
        out1[a] = mean_judge1
        eachtime2 = judge_2[:,a]
        mean_judge2 = np.nanmean(eachtime2)
        out2[a] = mean_judge2    
        r_wear[a] = np.mean([mean_judge1,mean_judge2])
        
        if r_wear[a] >= ratio:#閾値よりも高い場合
            if data_array[a] == 0:#閾値よりも高いというif文の中で、その時のdata_1minが[0]だったら
               corrected_prob = np.append(corrected_prob,1)#[1]で埋める（本当は補間でもいい）
            else:#閾値よりも高い中で、その時のdata_1minが[0]でない（計測できている）
                corrected_prob = np.append(corrected_prob,data_array[a])#元々のdata_1minの値が採用される
        else:
            corrected_prob = np.append(corrected_prob,0)#閾値よりも低い（非着用区間と判断）場合 
   
    fin_zeros = np.zeros(1440-(j+1))
    corrected_prob = np.append(corrected_prob,fin_zeros)

    return corrected_prob
#%%
def zeroConsec(data_array):

    frame_len=len(data_array)
    label= np.zeros((frame_len,))
    label[data_array > 0] = 1
    label[data_array == 0] = 0
    label_count = np.empty(0)

    for j in range(len(label)):
        if j == 0:
            label_count = np.append(label_count,1)
        else:
            param = label[j]+label[j-1]
            if param == 0:
                indata = label_count[j-1]+1
                label_count = np.append(label_count,indata)
            else:
                label_count = np.append(label_count,1)


    zero_count = np.empty(0)
    for j in range(len(label_count)-1):
        diff = label_count[j] - label_count[j+1]+1
        zero_count = np.append(zero_count,diff)   
    zero_count = np.append(zero_count,label_count[-1])

    corrected_consec_binary = np.ones((frame_len))
    over_th_idx = np.array(np.where(zero_count >=10))
    over_th_idx = over_th_idx.T
    over_th = zero_count[over_th_idx]

    for j in range(len(over_th)):
        corrected_consec_binary[int(over_th_idx[j,0]-over_th[j,0]+1):int(over_th_idx[j,0]+1)]=0
    
    
    return corrected_consec_binary
#%%
def zeroSynth(corrected_prob_copy, corrected_consec_binary):
    corrected_prob_copy[corrected_consec_binary == 0]=0;
    
    return corrected_prob_copy
