#./stonne -SparseGEMM -M=4 -N=4 -K=256 -num_ms=8 -dn_bw=8 -rn_bw=8 -rn_bw=8 -MK_sparsity=80 -KN_sparsity=10 -dataflow=MK_STA_KN_STR 

#-optimize=1
./stonne -CONV -R=3 -S=3 -C=6 -G=1 -K=6 -N=1 -X=8 -Y=8 -T_R=3 -T_S=3 -T_C=1 -T_G=1 -T_K=1 -T_N=1 -T_X_=1 -T_Y_=1 -num_ms=64 -dn_bw=8

#./stonne -FC -M=2 -K=4 -N=1024 -T_K=1 -T_N=1 -num_ms=64 -dn_bw=8
#./stonne -SparseGEMM -M=160 -N=80 -K=256 -num_ms=128 -dn_bw=64 -rn_bw=64  -MK_sparsity=80 -KN_sparsity=90 -dataflow=MK_STA_KN_STR

#./stonne -DenseGEMM -M=128 -N=128 -K=16 -num_ms=4 -dn_bw=4 -rn_bw=4  -T_N=1 -T_M=1 -T_K=4 -accumulation_buffer=1

#./stonne -DenseGEMM -M=4 -N=4 -K=16 -num_ms=4 -dn_bw=4 -rn_bw=4  -T_N=4 -T_M=1 -T_K=1 -accumulation_buffer=1 -rn_type="TEMPORALRN"

#./stonne -DenseGEMM -M=4 -N=4 -K=16 -ms_rows=4 -ms_cols=4 -dn_bw=8 -rn_bw=16  -T_N=4 -T_M=1 -T_K=1 -accumulation_buffer=1 -rn_type="TEMPORALRN" -mn_type="OS_MESH" -mem_ctrl="TPU_OS_DENSE"


#./stonne -DenseGEMM -M=5 -N=2 -K=2 -ms_rows=4 -ms_cols=4 -dn_bw=8 -rn_bw=16  -T_N=4 -T_M=4 -T_K=1 -accumulation_buffer=1 -rn_type="TEMPORALRN" -mn_type="OS_MESH" -mem_ctrl="TPU_OS_DENSE"

