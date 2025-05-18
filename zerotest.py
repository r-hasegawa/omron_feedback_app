import numpy as np

def zeroConsec_1(data_array):
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



def zeroConsec_2(data_array):

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


    print(label_count)
    print(zero_count)
    print(over_th_idx)


    for j in range(len(over_th)):
        corrected_consec_binary[int(over_th_idx[j,0]-over_th[j,0]+1):int(over_th_idx[j,0]+1)]=0
    
    
    return corrected_consec_binary



data = np.random.choice([0, 0, 0, 1], size=50)
print(data)
print(zeroConsec_1(data))
print(zeroConsec_2(data))