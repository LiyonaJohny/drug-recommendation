"""drugrecomendation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from drugrecomendationapp.views import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',index,name="index"),
    path('index/',index,name="index"),
    path('userreg/',userreg,name="userreg"),
    path('companyreg/',companyreg,name="companyreg"),
    path('userregistration/',userregistration,name="userregistration"),
    path('companyregistration/',companyregistration,name="companyregistration"),
    path('login/',login,name="login"),
    path('loginuser/',loginuser,name="loginuser"),
    path('logout/',logout_view,name="logout"),
    path('userhome/',userhome,name="userhome"),
    path('companyhome/',companyhome,name="companyhome"),
    path('viewcompany/',viewcompany,name="viewcompany"),
    path('companyupdation/',companyupdation,name="companyupdation"),
    path('companyupdate/',companyupdate,name="companyupdate"),
    path('companyupdation1/',companyupdation1,name="companyupdation1"),
    path('viewuser/',viewuser,name="viewuser"),
    path('userupdate/',userupdate,name="userupdate"),
    path('userupdation1/',userupdation1,name="userupdation1"), 
    path('adminhome/',adminhome,name="adminhome"),  
    path('adminviewcompany/',adminviewcompany,name="adminviewcompany"), 
    path('approvecompany/',approvecompany,name="approvecompany"),
    path('rejectcompany/',rejectcompany,name="rejectcompany"),
    path('addmedicine/',addmedicine,name="addmedicine"),
    path('vmedicine/',vmedicine,name="vmedicine"),
    path('med/',med,name="med"),
    path('viewmedicine/',viewmedicine,name="viewmedicine"),
    # path('medupdate/',medupdate,name="medupdate"),
    path('medicineupdate/',medicineupdate,name="medicineupdate"),
    path('medupdation/',medupdation,name="medupdation"),
    path('smedicine/',smedicine,name="smedicine"),
    path('review/',review,name="review"),
    path('doctorreg/',doctorreg, name='doctorreg'),
    path('doctorregistration/',doctorregistration,name= "doctorregistration"),
    path('adminviewdoctor/',adminviewdoctor,name='adminviewdoctor'),
    path('approvedoctor/',approvedoctor,name='approvedoctor'),
    path('doctorhome/',doctorhome,name='doctorhome'),
    path('rejectdoctor/',rejectdoctor,name='rejectdoctor'),
    path('viewdoctor/',viewdoctor,name='viewdoctor'),
    path('doctorupdation/',doctorupdation,name='doctorupdation'),
    path('doctorupdate/',doctorupdate,name='doctorupdate'),
    path('chat/',chat,name='chat'),
    path('chataction/',chataction,name='chataction'),
    path('doctorlist/',doctorlist,name='doctorlist'),
    path('userlist/',userlist,name='userlist'),
    path('dchat/',dchat,name='dchat'),
    path('dchataction/',dchataction,name='dchataction'),
    path('meddetail/',meddetail,name='meddetail'),
    path('givefeedback/',givefeedback,name='givefeedback'),
    path('viewfeedback/',viewfeedback,name='viewfeedback'),
    path('admin_viewfeedback/',admin_viewfeedback,name='admin_viewfeedback'),
    path('newsdetail/',newsdetail,name='newsdetail'),


]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns +=staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns +=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    urlpatterns +=static(settings.MEDIA_URL,document_root=settings.STATIC_ROOT)
    urlpatterns +=staticfiles_urlpatterns()


