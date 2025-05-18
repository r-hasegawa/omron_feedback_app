import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
#import japanize_matplotlib
from more_itertools import locate
#%%
def optimTh(data_array):
    
    i = 0
    while True:
        tmets = data_array[i]
        i += 1
        if tmets != 0:
            break
    i = i - 1
    j = 1439 
    while True:
        tmets = data_array[j]
        j -= 1    
        if tmets != 0:
            break
    j = j + 1
    trackingdata = data_array[i:j]
    zeronum = len(trackingdata)-np.count_nonzero(trackingdata)
    active = np.where(trackingdata > 1.5)
    numsed = len(trackingdata) -  len(active)
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
    while True: 
    #breakまで無限ループの繰り返し
        tmets = data_array[i]
        #print(i)
        i += 1  # i = i+ 1 に同じ
        if tmets != 0: # tmets が0と異なる場合
            break
        #ここで記録される[i]は最初に[0]以外の数字が出てくるフレーム数
    i = i - 1
    
    j = 1439 
    while True:
        tmets = data_array[j]
        #print(j)
        j -= 1    
        if tmets != 0:
            break
        #ここで記録される[j]は最後に[0]以外の数字が出てくるフレーム数
    j = j + 1
    
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
        print(a, len(hourdata), xx)
        # print(a, xx)


    print(i, data_array[i-3:i+4])
    print(j, data_array[j-3:j+4])

    judge_3 = np.zeros(1440)
    judge_3[:] = np.nan

    for a in range(i,j+1):
        start = a - define_range
        end = a + define_range      
        if start < i:
            start = i
        if end > j:
            end = j
              
        hourdata = data_array[start:end]
        nonzeronum = np.count_nonzero(hourdata) + np.count_nonzero(data_array[a])
        xx = nonzeronum/len(hourdata)
        judge_3[a] = xx


    print(judge_3)

    # for tes in range(i,j-define_range+1):
    #     print(judge_1[tes:])


    plt.imshow(judge_1, cmap='inferno', interpolation='nearest')
    plt.imshow(judge_2, cmap='inferno', interpolation='nearest')
    plt.colorbar()  # カラーバーを表示
    plt.title("2D Heatmap")
    # plt.show()

    # fig, (ax1,ax2,ax3,ax4,ax5) = plt.subplots(5,1,sharex = True)
    # ax1.plot(original)#オリジナルデータ
    # plt.show()



    def check_rows_equal(arr1, arr2, i, j):
        return np.array_equal(arr1[i], arr2[j], True)

    def check_columns_equal(arr1, arr2, i, j):
        return np.array_equal(arr1[:, i], arr2[:, j], True)

    test1 = i
    test2 = test1 + 59

    false_count = 0
    true_count = 0

    for test1 in range(1440-59):
        arr1 = judge_1[test1]
        arr2 = judge_2[test1 + 59]
        if(np.array_equal(arr1, arr2, True)):
            true_count += 1
        else:
            false_count += 1
            print(i,j,test1, test1+59, np.array_equal(arr1, arr2, True))


    print(true_count, false_count, true_count+false_count)

            
    
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

        # print(a, np.count_nonzero(np.isnan(eachtime1)), mean_judge1,
        #     np.count_nonzero(np.isnan(eachtime2)), mean_judge2, r_wear[a], judge_3[a])
        
        if r_wear[a] >= ratio:#閾値よりも高い場合
            if data_array[a] == 0:#閾値よりも高いというif文の中で、その時のdata_1minが[0]だったら
               corrected_prob = np.append(corrected_prob,1)#[1]で埋める（本当は補間でもいい）
            else:#閾値よりも高い中で、その時のdata_1minが[0]でない（計測できている）
                corrected_prob = np.append(corrected_prob,data_array[a])#元々のdata_1minの値が採用される
        else:
            corrected_prob = np.append(corrected_prob,0)#閾値よりも低い（非着用区間と判断）場合 
   
    fin_zeros = np.zeros(1440-(j+1))
    corrected_prob = np.append(corrected_prob,fin_zeros)

    if visualize == 1:
        plt.figure()
        ax1=plt.subplot(2,1,1)       
        plt.plot(r_wear)
        plt.plot([r_wear[0],r_wear[len(r_wear)-1]],[ratio, ratio],color='black',linestyle='dotted')
        plt.grid()
        plt.ylim(0,1.1)
        plt.xlim(i-60,j+60)
        plt.ylabel("Mounting probability")
        
        plt.subplot(2,1,2, sharex=ax1)
        plt.plot(data_array,color = "k",label='raw data')
        plt.plot(corrected_prob,color = "r",label='Corrected')
        plt.grid()
        plt.ylabel("METs")
        plt.legend(loc="upper left", fontsize=10)
        

    return corrected_prob
#%%

def zeroConsec(data_array):
    frame_len = len(data_array)

    # 0と1にラベル化
    label = np.where(data_array > 0, 1, 0)

    # 0の連続する長さを計算
    zero_count = np.zeros(frame_len)
    zero_run_lengths = []
    count = 0

    for i in range(frame_len):
        if label[i] == 0:
            count += 1
        else:
            if count > 0:
                zero_run_lengths.append((i - count, i - 1, count))
            count = 0
    if count > 0:  # 終了時に0が連続している場合
        zero_run_lengths.append((frame_len - count, frame_len - 1, count))

    # 連続する0の長さが10以上の箇所を特定して修正
    corrected_consec_binary = np.ones(frame_len)
    for start, end, length in zero_run_lengths:
        if length >= 10:
            corrected_consec_binary[start:end + 1] = 0

    return corrected_consec_binary

def zeroConsec_old(data_array):

    frame_len=len(data_array)
    label= np.zeros((frame_len,))
    label[data_array > 0] = 1
    label[data_array == 0] = 0

    # 0が連続して出現した回数を記録
    label_count = np.empty(0)

    for j in range(len(label)):
        if j == 0:
            label_count = np.append(label_count,1)
        else:
            param = label[j]+label[j-1]
            if param == 0:
                # 0が連続していた場合
                indata = label_count[j-1]+1
                label_count = np.append(label_count,indata)
            else:
                # 0→1 or 1→0 or 1→1
                label_count = np.append(label_count,1)

    # print(label[-20:])
    # print(label_count[-20:])

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

#%%
def breaks(frame,synth_data,visualize):
    
    frame_len = len(synth_data)
    label= np.zeros((frame_len,))-1
    sed = list(locate(synth_data, lambda x: 1.5 >= x >= 1.0)) #Sedentaryの検出
    label[sed] = 0
    
    #2分以上続くSedentaryの検出
    #現在のMetsと、次のMetsを取りに行って二つともがsedentaryの範囲に入れば0を割り振る
    for i in range(frame_len-1):
        ini = synth_data[i]
        fin = synth_data[i+1]
        if 1.5 >= ini >= 1.0 and 1.5 >= fin >= 1.0:
           label[i] = 1
           label[i+1] = 1
           
    over2sed = list(locate(label,lambda x: x==1)) #sedentaryは「0」とする
    
    light = list(locate(synth_data, lambda x: 2.9 >= x >= 1.6)) #Lightの検出
    label[light] = 2 #lightは「1」とする
    
    mv = list(locate(synth_data, lambda x: x >= 3.0)) #moderateの検出
    label[mv] = 3 #moderateは「2」とする
 
    #パターンの設定
    pat1 = np.array([1,2,1]) #[1,2,1]は[2分以上続くsedentary light 2分以上続くsedentary]
    for i in range(len(label)-2):
        pat_roi = label[i:i+3]
        if all(np.equal(pat_roi,pat1))==True:
            label[i:i+3,] = 1 
            
    if visualize == 1:
        temp = np.where(~np.isnan(label))
        temp=temp[0]
        ini = temp[0]
        fin = temp[len(temp)-1]
        plt.tight_layout()
        plt.figure()
        plt.subplot(2,1,1)
        plt.plot(frame,synth_data)
        plt.xticks([])
        plt.xticks()
        plt.scatter(frame[sed],synth_data[sed],c='magenta',s=5,label="Sedentary")
        plt.scatter(frame[over2sed],synth_data[over2sed],c='gold',s=5,label="2分以上続くSedentary")
        plt.xlim(ini-60,fin+60)   
        plt.scatter(frame[light],synth_data[light],c='indianred',s=5,label="Light")
        plt.legend()
        plt.subplot(2,1,2)
        plt.plot(frame,label,'-o')
        plt.yticks([-1,0,1,2,3],["Non-wear","Sedentary","2min-consective Sed.","Light","MVPA"])
        plt.xlim(ini-60,fin+60)
        plt.ylim([-1.2,3.2])
        plt.xticks([])
    
    return label
#%%
def visualize(original,corrected_prob,corrected_consec_binary,synth_data,label) :
    fig, (ax1,ax2,ax3,ax4,ax5) = plt.subplots(5,1,sharex = True)
    ax1.plot(original)#オリジナルデータ
    ax1.grid()
    ax2.plot(corrected_prob)#手法①確率ジャッジ
    ax2.grid()
    ax3.plot(corrected_consec_binary)#手法②ゼロの連続
    ax3.grid()
    ax4.plot(synth_data)#手法①②統合
    ax4.grid()
    ax5.plot(label)#ラベルデータ
    ax5.grid()
    # plt.show()

#%%