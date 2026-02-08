from jsonserv.community import viewsets


# REST-сервисы
router_urls = {
    'rest/comment': viewsets.CommentViewSet,
    'rest/letter': viewsets.LetterViewSet,
    'rest/objecttask': viewsets.ObjectTaskViewSet,
    'rest/task': viewsets.TaskViewSet,
    'rest/taskrefer': viewsets.TaskReferViewSet,
    'rest/taskuser': viewsets.TaskUserViewSet
}
