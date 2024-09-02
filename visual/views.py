from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.

def main(request):
    return render(request,'base.html')

from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import cv2
import os
import numpy as np
import torch




model = torch.load(settings.YOLOV8_WEIGHTS_PATH)
model.eval()




VIDEO_FILE_PATH = os.path.join(settings.MEDIA_ROOT, 'output.avi')
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_writer = cv2.VideoWriter(VIDEO_FILE_PATH, fourcc, 1, (640, 480))

@csrf_exempt
def upload_frame(request):
    if request.method =='POST' and 'file' in request.FILES:
        file = request.FILES['file']
        timestamp = request.POST.get('timestamp','')
        filename = f'frame_{timestamp}.jpg'
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        img = cv2.imread(file_path)
        if img is not None:
            video_writer.write(img)
        
        return HttpResponse('프레임 업로드 성공', status=200)
    return HttpResponse('잘못된 요청', status = 400)

def cleanup():
    global video_writer
    if video_writer is not None:
        video_writer.release()
        cv2.destroyAllWindows()

from django.http import JsonResponse

@csrf_exempt
def upload_frame(requset):
    if requset.method =='POST':
        file = requset.FILES.get('file')
        if file:

            np_array = np.frombuffer(file.read(), np.uint8)
            frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

            results = model.detect(frame)

            reaction_value = evaluate_detections(results)

            send_reaction_to_arduino(reaction_value)

            return JsonResponse({'status':'sucess','reaction_value':reaction_value})
        return JsonResponse({'status':'error','message':'No file uploaded'}, status=400)
    return JsonResponse({'status':'error','message':'Invalid request method'}, status = 405)



from datetime import datetime, timedelta
greenlight = 0

def evaluate_detections(detections):
    greenlight_time = 0
    crosswalk_center = 0
    reaction_value = 0
    previous_detection = 0
    global greenlight    

    for detection in detections:
    
        label, confidence, bbox = detection
        
        #전제 조건은 보행 신호 초록등이 들어온 이후부터 작동

        if label =='greenlight' and confidence>0.9 and greenlight==0:
            if not greenlight_time:
                greenlight_time = datetime.now()
                greenlight = 1
            

        if label == 'whitecane' and confidence>0.7 and greenlight==1: #wheelchair/ whitecane 등 특정 조건에 따라 반응을 돌려줄 코드 
            
            #소리 출력 하는 아두이노 포트 번호 활성화 하는 코드
            if reaction_value != 5:
                reaction_value = 5

        if label == 'crosswalk' and confidence >0.7:
            crosswalk_center = get_crosswalk_center(bbox)


    if greenlight==1:
        # 1) 두 카메라 사이 인식된 객체가 없어지지 않는다면 3~5초 연장
        # 2) 두 카메라 사이 인식된 객체 7초간 거리 측정을 통해 속도 계산(제일 변화가 없는 객체), 도달 시간 예상 하여 신호등 시간 도출 아두이노로 전달
        
        # 1) 5초 단위로 person, whitecane, wheelchair 감지 있는 경우 3~5초 상황에 따라 연장
        if reaction_value ==5: #whitecane이라면..5초마다 확인 시간 연장()
            if greenlight_time and datetime.now()>= greenlight_time + timedelta(seconds=5):
                light_time = 5
        else:
            if greenlight_time and datetime.now()>= greenlight_time + timedelta(seconds=14):
                light_time = 3

   
   
   
   
        # 2)
        # if greenlight_time and datetime.now() >= greenlight_time + timedelta(seconds=7):
        #     # 초록불이고 7초가 지난 상태면 횡단보도와 제일 가까운 사람 
        #     closest_object1 = select_target_object(detections)
            

        #     if closest_object1:
        #         closest_object_postion1 = get_object_position(closest_object1)
        #         object_speed = calculate_distance(closest_object_postion1, crosswalk_center)
            
        # # 초록불이고 14초가 지난 상태에서 재측정
        # if greenlight_time and datetime.now() >=greenlight_time + timedelta(seconds=14):
        #     closest_object2 = select_target_object(detections)
            
        #     if closest_object2:
        #         closest_object_postion2 = get_object_position(closest_object2)
        #         object_speed = calculate_distance(closest_object_postion2, crosswalk_center)

        # #변동 사항이 있으면 변경
        # if closest_object1 and closest_object2:
        #     if closest_object1 != closest_object2:
        #         object_speed = calculate_distance(closest_object_postion2, crosswalk_center)

    
    


#객체 인식 결과에서 특정 객체를 선택하는 로직        
def select_target_object(detections):
    for detection in detections:
        label, confidence, bbox = detection
        if (label == 'person')or(label=='whitecane')or(label=='wheelchair'):
            return detection
    
    return None


#객치의 위치(중심점) 계산
def get_object_position(detection):
    _,_,bbox = detection
    x_center =  (bbox[0]+bbox[2])/2
    y_center =  (bbox[1]+bbox[3])/2 
    return (x_center, y_center)

def get_crosswalk_center(bbox):
    x_center = (bbox[0]+bbox[2])/2
    y_top = bbox[1]
    return (x_center, y_top)


def calculate_distance(pos1, pos2):
    
    return ((pos2[0]-pos1[0])**2 + (pos2[1]-pos1[1])**2)**0.5