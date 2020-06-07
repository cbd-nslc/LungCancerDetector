import os
DSB_ROOT = os.path.dirname(os.path.abspath(__file__))

num_workers = 0

config_submit = {'detector_model': 'net_detector',
                 'detector_param': DSB_ROOT + '/model/detector.ckpt',
                 'classifier_model': 'net_classifier',
                 'classifier_param': DSB_ROOT + '/model/classifier.ckpt',
                 'n_gpu': 1,
                 'n_worker_preprocessing': None,
                 'use_exsiting_preprocessing': False,
                 'skip_preprocessing': False,
                 'skip_detect': False,}

config_training = {'stage1_data_path': '/work/DataBowl3/stage1/stage1/',
                   'luna_raw': '/work/DataBowl3/luna/raw/',
                   'luna_segment': '/work/DataBowl3/luna/seg-lungs-LUNA16/',
                   'luna_data': '/work/DataBowl3/luna/allset',
                   'preprocess_result_path': '/work/DataBowl3/stage1/preprocess/',
                   'luna_abbr': './detector/labels/shorter.csv',
                   'luna_label': './detector/labels/lunaqualified.csv',
                   'stage1_annos_path': ['./detector/labels/label_job5.csv',
                                         './detector/labels/label_job4_2.csv',
                                         './detector/labels/label_job4_1.csv',
                                         './detector/labels/label_job0.csv',
                                         './detector/labels/label_qualified.csv'],
                   'bbox_path': '../detector/results/res18/bbox/',
                   'preprocessing_backend': 'python'
                   }
