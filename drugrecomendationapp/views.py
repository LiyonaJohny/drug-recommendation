from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect,redirect
from django.db import connection
from drugrecomendationapp.forms import mform
from drugrecomendationapp.models import mmodel
import nltk
from django.db import connection
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
stop_words = set(stopwords.words('english'))
txt = "Programers  is an program with programing languages. anila was good programmer "
from nltk.stem import PorterStemmer
import datetime
from functools import wraps
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
import requests
tdate=datetime.date.today()
today=tdate.strftime("%Y-%m-%d")
todaym=tdate.strftime("%m")

# ---------------------------------------------------------------------------
# Access control: every dashboard view should require a logged-in session of
# the matching role. Call require_role() with no arguments to only require
# that *some* valid session exists (any of the four roles).
# ---------------------------------------------------------------------------
def require_role(*roles):
    def decorator(viewfunc):
        @wraps(viewfunc)
        def wrapper(request, *args, **kwargs):
            utype = request.session.get('utype')
            if not utype:
                return redirect('/login/')
            if roles and utype not in roles:
                msg = "<script>alert('You are not authorized to view that page.');window.location='/index/';</script>"
                return HttpResponse(msg)
            return viewfunc(request, *args, **kwargs)
        return wrapper
    return decorator


def logout_view(request):
    request.session.flush()
    return redirect('/index/')


# ---------------------------------------------------------------------------
# Password hashing with a transparent upgrade path: rows created before this
# change store the password in plain text. On a successful login with a
# legacy plain-text row we re-hash it in place, so every account migrates to
# a proper hash the first time its owner logs in, without ever locking
# anyone out.
# ---------------------------------------------------------------------------
def _password_matches(cursor, lid, stored_pw, submitted_pw):
    if stored_pw.startswith(('pbkdf2_', 'argon2', 'bcrypt', 'sha1$')):
        return check_password(submitted_pw, stored_pw)
    if stored_pw == submitted_pw:
        cursor.execute("update login set upass=%s where lid=%s", [make_password(submitted_pw), lid])
        return True
    return False

# Create your views here.
def index(request):
    return render(request,"index.html")

def userreg(request):
    return render(request,"userreg.html")

def companyreg(request):
    return render(request,"companyreg.html")



def userregistration(request):
    cursor=connection.cursor()
    na=request.POST['name']
    ag=request.POST['age']
    gen=request.POST['gender']
    pl=request.POST['place']
    ad=request.POST['address']
    ph=request.POST['phone']
    em=request.POST['email']
    pw=request.POST['pwd']
    hashed=make_password(pw)

    sql="insert into user(uname,age,gender,place,address,phonenum,email,password) values(%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql,[na,ag,gen,pl,ad,ph,em,hashed])
    uid=cursor.lastrowid
    sql3="insert into login(uid,uname,upass,utype,status) values (%s,%s,%s,%s,%s)"
    cursor.execute(sql3,[uid,em,hashed,'user',''])

    msg="<script>alert('User Registered Successfully!');window.location='/index/';</script>"
    return HttpResponse(msg)

def companyregistration(request):
    cursor=connection.cursor()
    na=request.POST['name']
    pl=request.POST['place']
    ad=request.POST['address']
    ph=request.POST['phone']
    em=request.POST['email']
    pw=request.POST['pwd']
    hashed=make_password(pw)

    sql="insert into company(cname,place,address,phonenum,email,password) values(%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql,[na,pl,ad,ph,em,hashed])
    cid=cursor.lastrowid
    sql3="insert into login(uid,uname,upass,utype,status) values (%s,%s,%s,%s,%s)"
    cursor.execute(sql3,[cid,em,hashed,'company','false'])

    msg="<script>alert('company Registered Successfully!');window.location='/index/';</script>"
    return HttpResponse(msg)


def login(request):
    return render(request,"login.html")
def loginuser(request):
    cursor=connection.cursor()
    p=request.POST['name']
    q=request.POST['pwd']
    sql="select * from login where uname=%s"
    cursor.execute(sql,[p])
    result=cursor.fetchall()

    matched=None
    for row in result:
        if _password_matches(cursor, row[0], row[3], q):
            matched=row
            break

    if not matched:
        msg="<script>alert('Invalid username and password');window.location='/login/';</script>"
        return HttpResponse(msg)

    row=matched
    request.session['uid']=row[1]
    request.session['uname']=row[2]
    request.session['utype']=row[4]
    status=row[5] if len(row) > 5 else ''

    if(row[4]=='company'):
        if(status=='true'):
            return render(request,'companyhome.html')
        request.session.flush()
        msg="<script>alert('Your company account is still awaiting admin approval.');window.location='/login/';</script>"
        return HttpResponse(msg)

    elif(row[4]=='doctor'):
        if(status=='true'):
            return render(request,'doctorhome.html')
        request.session.flush()
        msg="<script>alert('Your doctor account is still awaiting admin approval.');window.location='/login/';</script>"
        return HttpResponse(msg)

    elif(row[4]=='user'):
        return render(request,'userhome.html')

    elif(row[4]=='admin'):
        return render(request,'adminhome.html')

    request.session.flush()
    msg="<script>alert('Invalid username and password');window.location='/login/';</script>"
    return HttpResponse(msg)
        
@require_role('company')
def companyhome(request):
    return render(request,"companyhome.html")

@require_role('company')
def viewcompany(request):
    cursor=connection.cursor()
    uid=request.session['uid']
    s="select * from company where cid=%s"
    cursor.execute(s,[uid])
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'cid':row[0],'cname':row[1],'place':row[2],'address':row[3],'phonenum':row[4],'email':row[5]}
        use.append(q)
    return render(request,'viewcompany.html',{'use':use})

@require_role('user')
def userhome(request):
    return render(request,'userhome.html')
def _stars(rate):
    try:
        return max(0, min(5, int(round(float(rate)))))
    except (TypeError, ValueError):
        return 0

@require_role()
def vmedicine(request):
    cursor=connection.cursor()

    s="""
        SELECT med_details.med_id, med_details.name, med_details.used, med_details.mg,
               med_details.dosage, med_details.cmp, med_details.effects, med_details.pres,
               med_details.pack, med_details.image,
               COALESCE(AVG(review.rating), 0) AS rate,
               COUNT(review.rid) AS rcount
        FROM med_details
        LEFT JOIN review ON review.med_id = med_details.med_id
        GROUP BY med_details.med_id
        ORDER BY rate DESC
    """
    cursor.execute(s)
    rs=cursor.fetchall()
    tk=[]
    for row in rs:
        q={'med_id':row[0],'name':row[1],'used':row[2],'mg':row[3],'dosage':row[4],'cmp':row[5],'effects':row[6],'pres':row[7],'pack':row[8],'image':row[9],'rating':row[10],'rcount':row[11],'filled_stars':_stars(row[10])}
        tk.append(q)
    return render(request,'vmedicine.html',{'tk':tk})

@require_role()
def meddetail(request):
    cursor=connection.cursor()
    mid=request.GET['mid']
    s="""
        SELECT med_details.med_id, med_details.name, med_details.used, med_details.mg,
               med_details.dosage, med_details.cmp, med_details.effects, med_details.pres,
               med_details.pack, med_details.image,
               COALESCE(AVG(review.rating), 0) AS rate,
               COUNT(review.rid) AS rcount
        FROM med_details
        LEFT JOIN review ON review.med_id = med_details.med_id
        WHERE med_details.med_id=%s
        GROUP BY med_details.med_id
    """
    cursor.execute(s,[mid])
    rs=cursor.fetchall()
    tk=[]
    for row in rs:
        q={'med_id':row[0],'name':row[1],'used':row[2],'mg':row[3],'dosage':row[4],'cmp':row[5],'effects':row[6],'pres':row[7],'pack':row[8],'image':row[9],'rating':row[10],'rcount':row[11],'filled_stars':_stars(row[10])}
        tk.append(q)
    s="select * from review where med_id=%s order by date desc"
    cursor.execute(s,[mid])
    rs=cursor.fetchall()
    rv=[]
    for row in rs:
        q={'rid':row[0],'uid':row[1],'med_id':row[2],'date':row[3],'review':row[4],'rating':row[5]}
        rv.append(q)

    return render(request,'meddetail.html',{'tk':tk,'rv':rv,'mid':mid})

@require_role('company')
def companyupdation(request):
    cursor=connection.cursor()
    cpid=request.session['uid']
    s="select * from company where cid=%s"
    cursor.execute(s,[cpid])
    rs=cursor.fetchall()
    tk=[]
    for row in rs:
        q={'cid':row[0],'cname':row[1],'place':row[2],'address':row[3],'phonenum':row[4],'email':row[5]}
        tk.append(q)
    return render(request,'companyupdation.html',{'tk':tk})

@require_role('company')
def companyupdate(request):
    cursor=connection.cursor()
    cpid=request.session['uid']
    s="select * from company where cid=%s"
    cursor.execute(s,[cpid])
    rs=cursor.fetchall()
    tk=[]
    for row in rs:
        q={'cid':row[0],'cname':row[1],'place':row[2],'address':row[3],'phonenum':row[4],'email':row[5]}
        tk.append(q)
    return render(request,'companyupdation.html',{'tk':tk})

@require_role('company')
def companyupdation1(request):
    cursor=connection.cursor()
    cpid=request.session['uid']
    name=request.POST['name']
    place=request.POST['place']
    address=request.POST['address']
    phoneno=request.POST['phone']
    email=request.POST['email']
    sql="update company set cname=%s,place=%s,address=%s,phonenum=%s,email=%s where cid=%s"
    cursor.execute(sql,[name,place,address,phoneno,email,cpid])
    msg="<script>alert('Updated Successfully!');window.location='/companyhome/';</script>"
    return HttpResponse(msg)

@require_role('admin')
def viewuser(request):
    cursor=connection.cursor()
    s="select * from user "
    cursor.execute(s)
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'uid':row[0],'uname':row[1],'age':row[2],'gender':row[3],'place':row[4],'address':row[5],'phonenum':row[6],'email':row[7]}
        use.append(q)

    return render(request,'viewuser.html',{'use':use})

@require_role('user')
def userupdate(request):
    cursor=connection.cursor()
    usid=request.session['uid']
    s="select * from user where uid=%s"
    cursor.execute(s,[usid])
    rs=cursor.fetchall()
    tk=[]
    for row in rs:
        q={'uid':row[0],'uname':row[1],'age':row[2],'gender':row[3],'place':row[4],'address':row[5],'phonenum':row[6],'email':row[7]}
        tk.append(q)
    return render(request,'updateuser.html',{'tk':tk})

@require_role('user')
def userupdation1(request):
    cursor=connection.cursor()
    usid=request.session['uid']
    name=request.POST['name']
    age=request.POST['age']
    gender=request.POST['gender']
    place=request.POST['place']
    address=request.POST['address']
    phoneno=request.POST['phone']
    email=request.POST['email']
    sql="update user set uname=%s,age=%s,gender=%s,place=%s,address=%s,phonenum=%s,email=%s where uid=%s"
    cursor.execute(sql,[name,age,gender,place,address,phoneno,email,usid])
    msg="<script>alert('Updated Successfully!');window.location='/userhome/';</script>"
    return HttpResponse(msg)

@require_role('admin')
def adminhome(request):
    return render(request,'adminhome.html')

@require_role('admin')
def adminviewcompany(request):
    cursor=connection.cursor()
    s="select * from company inner join login on login.uid=company.cid where login.utype='company'"
    cursor.execute(s)
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'cid':row[0],'cname':row[1],'place':row[2],'address':row[3],'phonenum':row[4],'email':row[5],'status':row[12]}
        use.append(q)
    return render(request,'adminviewcompany.html',{'use':use})

@require_role('admin')
def approvecompany(request):
    cursor=connection.cursor()
    cpid=request.GET['id']
    s="update login set status='true' where uid=%s and utype='company'"
    cursor.execute(s,[cpid])

    msg="<script>alert('Approved Successfully!');window.location='/adminviewcompany/';</script>"
    return HttpResponse(msg)

@require_role('admin')
def rejectcompany(request):
    cursor=connection.cursor()
    cpid=request.GET['id']
    s="update login set status='false' where uid=%s and utype='company'"
    cursor.execute(s,[cpid])

    msg="<script>alert('Company rejected.');window.location='/adminviewcompany/';</script>"
    return HttpResponse(msg)

@require_role('company')
def addmedicine(request):
    return render(request,"addmedicine.html")

# def meddetails(request):
#     cursor=connection.cursor()
#     na=request.GET['name']
#     us=request.GET['used']
#     mg=request.GET['mg']
#     ds=request.GET['dosage']
#     cmp=request.GET['cmp']
#     eff=request.GET['effects']
#     pr=request.GET['pres']
#     pk=request.GET['pack']
#     img=request.GET['image']

#     sql="insert into med_details(name,used,mg,dosage,cmp,effects,pres,pack,image) values('%s','%s','%s','%s','%s','%s','%s','%s','%s')"%(na,us,mg,ds,cmp,eff,pr,pk,img)
#     cursor.execute(sql)

#     msg="<script>alert('Details added Successfully!');window.location='/companyhome/';</script>"
#     return HttpResponse(msg)

@require_role('company')
def viewmedicine(request):
    cursor=connection.cursor()
    s="select * from med_details"
    cursor.execute(s)
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'med_id':row[0],'name':row[1],'used':row[2],'mg':row[3],'dosage':row[4],'cmp':row[5],'effects':row[6],'pres':row[7],'pack':row[8],'image':row[9]}
        use.append(q)

    return render(request,"viewmedicine.html",{'use':use})

@require_role('company')
def med(request):
    if request.method=="POST":
        medforms=mform(request.POST,request.FILES)
        if medforms.is_valid ():
            meds=mmodel()
            meds.name=request.POST['name']
            meds.used=request.POST['used']
            meds.mg=request.POST['mg']
            meds.dosage=request.POST['dosage']
            meds.cmp=request.POST['cmp']
            meds.effects=request.POST['effects']
            meds.pres=request.POST['pres']
            meds.pack=request.POST['pack']
            meds.image=medforms.cleaned_data["image"]

            meds.save()
            msg="<script>alert('successfully added');window.location='/addmedicine/';</script>"
            return HttpResponse(msg)

        else:
            msg="<script>alert('Please fill in every field correctly.');window.location='/addmedicine/';</script>"
            return HttpResponse(msg)

    return redirect('/addmedicine/')

@require_role('company')
def medicineupdate(request):
    cursor=connection.cursor()
    mid=request.GET['id']
    s="select * from med_details where med_id=%s"
    cursor.execute(s,[mid])
    rs=cursor.fetchall()
    tk=[]
    for row in rs:
        q={'med_id':row[0],'name':row[1],'used':row[2],'mg':row[3],'dosage':row[4],'cmp':row[5],'effects':row[6],'pres':row[7],'pack':row[8]}
        tk.append(q)
    return render(request,'medicineupdate.html',{'tk':tk})

@require_role('company')
def medupdation(request):
    cursor=connection.cursor()
    mid=request.POST['id']
    name=request.POST['mname']
    used=request.POST['used']
    mg=request.POST['mg']
    dosage=request.POST['dosage']
    cmp=request.POST['cmp']
    effects=request.POST['effects']
    pres=request.POST['pres']
    pack=request.POST['pack']
    sql1="update med_details set name=%s,used=%s,mg=%s,dosage=%s,cmp=%s,effects=%s,pres=%s,pack=%s where med_id=%s"
    cursor.execute(sql1,[name,used,mg,dosage,cmp,effects,pres,pack,mid])
    msg="<script>alert('Updated Successfully!');window.location='/viewmedicine/';</script>"
    return HttpResponse(msg)

# def medicine(request):
#     cursor=connection.cursor()
#     mid=request.GET['id']
#     s="select * from med_details where used='%s'"%(search)
#     cursor.execute(s)
#     rs=cursor.fetchall()
#     tk=[]
#     for row in rs:
#         q={'med_id':row[0],'name':row[1],'used':row[2],'mg':row[3],'dosage':row[4],'cmp':row[5],'effects':row[6],'pres':row[7],'pack':row[8]}
#         tk.append(q)
#     return render(request,'userhome.html',{'tk':tk})
@require_role()
def smedicine(request):
    cursor = connection.cursor()
    med = request.GET['med']

    s = """
        SELECT med_details.med_id,
               med_details.name,
               med_details.used,
               med_details.mg,
               med_details.dosage,
               med_details.cmp,
               med_details.effects,
               med_details.pres,
               med_details.pack,
               med_details.image,
               COALESCE(AVG(review.rating), 0) AS rate,
               COUNT(review.rid) AS rcount
        FROM med_details
        LEFT JOIN review ON review.med_id = med_details.med_id
        WHERE med_details.used LIKE %s
           OR med_details.name LIKE %s
        GROUP BY med_details.med_id
        ORDER BY rate DESC
        LIMIT 20;
    """
    like = '%' + med + '%'
    cursor.execute(s, [like, like])
    rs = cursor.fetchall()
    tk = []
    for row in rs:
        q = {
            'med_id': row[0],
            'name': row[1],
            'used': row[2],
            'mg': row[3],
            'dosage': row[4],
            'cmp': row[5],
            'effects': row[6],
            'pres': row[7],
            'pack': row[8],
            'image': row[9],
            'rating': row[10],
            'rcount': row[11],
            'filled_stars': _stars(row[10])
        }
        tk.append(q)

    return render(request, 'vmedicine.html', {'tk': tk, 'query': med})



def _score_with_service(drug_id, text, user_id):
    """Ask the review microservice to score (and store) the review.
    Returns the 1-5 rating, or None if the service is unreachable or errors."""
    try:
        resp = requests.post(
            settings.REVIEW_SERVICE_URL.rstrip('/') + '/reviews',
            json={'drug_id': int(drug_id), 'review': text, 'user_id': user_id},
            timeout=settings.REVIEW_SERVICE_TIMEOUT,
        )
        if resp.status_code == 201:
            return int(resp.json()['rating'])
    except (requests.RequestException, ValueError, KeyError):
        return None
    return None


def _score_with_nltk(cursor, text):
    """Fallback scorer: the original inline NLTK opinion-lexicon pipeline.
    Returns a 1-5 rating. Used when the microservice is unavailable."""
    cursor.execute("truncate table postag")
    for sentence in sent_tokenize(text):
        tokens = [w for w in nltk.word_tokenize(sentence) if w not in stop_words]
        tagged = [(w, t) for w, t in nltk.pos_tag(tokens) if t in (
            'NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'JJR', 'JJS',
            'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ')]
        for word, _tag in tagged:
            cursor.execute("insert into postag(data) values(%s)", [word])

    cursor.execute("select * from postag")
    sentence = ' '.join(r[1] for r in cursor.fetchall())

    ps = PorterStemmer()
    cursor.execute("truncate table stemming")
    for w in word_tokenize(sentence):
        cursor.execute("insert into stemming(data) values(%s)", [ps.stem(w)])

    cursor.execute("truncate table pword")
    cursor.execute("select * from stemming")
    for row in cursor.fetchall():
        cursor.execute("select * from positive")
        for row1 in cursor.fetchall():
            if row[1] == row1[1]:
                cursor.execute("insert into pword(pword) values(%s)", [row[1]])

    cursor.execute("truncate table nword")
    cursor.execute("select * from stemming")
    for row in cursor.fetchall():
        cursor.execute("select * from negative")
        for row1 in cursor.fetchall():
            if row[1] == row1[1]:
                cursor.execute("insert into nword(nword) values(%s)", [row[1]])

    cursor.execute("select count(*) from pword")
    pcount = cursor.fetchone()[0]
    cursor.execute("select count(*) from nword")
    ncount = cursor.fetchone()[0]

    total = float(pcount) + float(ncount)
    if total == 0:
        return 3
    avgcount = ((float(pcount) - float(ncount)) / total) / total
    if avgcount > 0.25:
        return 5
    elif 0.0 < avgcount < 0.25:
        return 4
    elif avgcount == -0.25:
        return 2
    elif avgcount < 0.25:
        return 1
    return 3


@require_role()
def review(request):
    cursor = connection.cursor()
    uid = request.session["uid"]
    na = request.POST['mid']
    re = request.POST['review']

    # Primary path: the scoring microservice (TF-IDF + Logistic Regression),
    # which also stores the review in MongoDB. Fall back to the inline NLTK
    # scorer when the service is down so reviews are never lost.
    rating = _score_with_service(na, re, uid)
    if rating is None:
        rating = _score_with_nltk(cursor, re)

    sql = "insert into review(uid,med_id,date,review,rating) values(%s,%s,%s,%s,%s)"
    cursor.execute(sql, [uid, na, today, re, rating])

    msg = "<script>alert('Review Added');window.location='/meddetail/?mid="+str(na)+"';</script>"
    return HttpResponse(msg)


from datetime import datetime


def doctorreg(request):
    return render(request,"doctorreg.html")

def doctorregistration(request):
    cursor=connection.cursor()
    na=request.POST['name']
    spl=request.POST['Specilization']
    nm=request.POST['number']
    ql=request.POST['qualification']
    em=request.POST['email']
    pw=request.POST['password']
    hashed=make_password(pw)

    sql="insert into doctor(name,specilization,license,qualification,email,password) values(%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql,[na,spl,nm,ql,em,hashed])
    doc_id=cursor.lastrowid
    sql3="insert into login(uid,uname,upass,utype,status) values (%s,%s,%s,%s,%s)"
    cursor.execute(sql3,[doc_id,em,hashed,'doctor','false'])
    msg="<script>alert('Doctor Registered Successfully!');window.location='/index/';</script>"
    return HttpResponse(msg)

@require_role('admin')
def adminviewdoctor(request):
    cursor=connection.cursor()
    s="select * from doctor inner join login on login.uid=doctor.doc_id where login.utype='doctor'"
    cursor.execute(s)
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'doc_id':row[0],'name':row[1],'specilization':row[2],'number':row[3],'qualification':row[4],'email':row[5],'status':row[12]}
        use.append(q)
    return render(request,'adminviewdoctor.html',{'use':use})

@require_role('admin')
def approvedoctor(request):
    cursor=connection.cursor()
    doc_id=request.GET['id']
    s="update login set status='true' where uid=%s and utype='doctor'"
    cursor.execute(s,[doc_id])

    msg="<script>alert('Approved Successfully!');window.location='/adminviewdoctor/';</script>"
    return HttpResponse(msg)

@require_role('admin')
def rejectdoctor(request):
    cursor=connection.cursor()
    doc_id=request.GET['id']
    s="update login set status='false' where uid=%s and utype='doctor'"
    cursor.execute(s,[doc_id])

    msg="<script>alert('Doctor rejected.');window.location='/adminviewdoctor/';</script>"
    return HttpResponse(msg)

@require_role('doctor')
def doctorhome(request):
    return render(request,"doctorhome.html")

@require_role('doctor')
def viewdoctor(request):
    cursor=connection.cursor()
    doc_id=request.session['uid']
    s="select * from doctor where doc_id=%s"
    cursor.execute(s,[doc_id])
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'doc_id':row[0],'name':row[1],'specilization':row[2],'number':row[3],'qualification':row[4],'email':row[5]}
        use.append(q)
    return render(request,'viewdoctor.html',{'use':use})

@require_role('doctor')
def doctorupdation(request):
    cursor=connection.cursor()
    doc_id=request.session['uid']
    s="select * from doctor where doc_id=%s"
    cursor.execute(s,[doc_id])
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'doc_id':row[0],'name':row[1],'specilization':row[2],'number':row[3],'qualification':row[4],'email':row[5]}
        use.append(q)
    return render(request,'doctorupdation.html',{'use':use})

@require_role('doctor')
def doctorupdate(request):
    cursor=connection.cursor()
    doc_id=request.session['uid']
    na=request.POST['name']
    spl=request.POST['specilization']
    nm=request.POST['number']
    ql=request.POST['qualification']
    em=request.POST['email']
    sql="update doctor set name=%s,specilization=%s,license=%s,qualification=%s,email=%s where doc_id=%s"
    cursor.execute(sql,[na,spl,nm,ql,em,doc_id])
    msg="<script>alert('Updated Successfully!');window.location='/viewdoctor/';</script>"
    return HttpResponse(msg)

@require_role()
def doctorlist(request):
    cursor=connection.cursor()
    s="select * from doctor"
    cursor.execute(s)
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'doc_id':row[0],'name':row[1],'specilization':row[2],'number':row[3],'qualification':row[4],'email':row[5]}
        use.append(q)
    return render(request,'doctorlist.html',{'use':use})


@require_role('user')
def chat(request):
    cursor=connection.cursor()
    lid=request.GET['lid']
    uid=request.session['uid']
    s="select chatm.chatid, chatm.uid, chatm.lid, chatm.chatdate, chats.msgid, chats.msg, chats.typ " \
      "from chatm inner join chats on chatm.chatid=chats.chatid " \
      "where chatm.lid=%s and chatm.uid=%s order by chatm.chatdate asc, chats.msgid asc"
    cursor.execute(s,[lid,uid])
    rs=cursor.fetchall()
    alist=[]
    for r in rs:
        x={'chatid':r[0],'chatdate':r[3],'msg':r[5],'typ':r[6]}
        alist.append(x)
    docname=lid
    s2="select name from doctor where doc_id=%s"
    cursor.execute(s2,[lid])
    rd=cursor.fetchone()
    if rd:
        docname=rd[0]
    return render(request,'chat.html',{'lid':lid,'uid':uid,'alist':alist,'docname':docname})

@require_role('user')
def chataction(request):
    cursor=connection.cursor()
    uid=request.session['uid']
    lid=request.POST['lid']
    msg=request.POST['msg']
    ss="select chatid from chatm where uid=%s and lid=%s and chatdate=%s"
    cursor.execute(ss,[uid,lid,today])
    row=cursor.fetchone()
    if row:
        chid=row[0]
    else:
        sql1="insert into chatm(uid,lid,chatdate) values(%s,%s,%s)"
        cursor.execute(sql1,[uid,lid,today])
        chid=cursor.lastrowid
    sql="insert into chats(chatid,msg,typ)values(%s,%s,'user')"
    cursor.execute(sql,[chid,msg])
    msg="<script>;window.location='/chat?lid="+lid+"';</script>"
    return HttpResponse(msg)

@require_role('doctor')
def userlist(request):
    cursor=connection.cursor()
    lid=request.session['uid']
    s="SELECT * FROM user where uid in(select uid from chatm where lid=%s)"
    cursor.execute(s,[lid])
    rs=cursor.fetchall()
    use=[]
    for row in rs:
        q={'uid':row[0],'uname':row[1],'age':row[2],'gender':row[3]}
        use.append(q)
    return render(request,'userlist.html',{'use':use})

@require_role('doctor')
def dchat(request):
    cursor=connection.cursor()
    lid=request.session['uid']
    uid=request.GET['uid']
    s="select chatm.chatid, chatm.uid, chatm.lid, chatm.chatdate, chats.msgid, chats.msg, chats.typ " \
      "from chatm inner join chats on chatm.chatid=chats.chatid " \
      "where chatm.lid=%s and chatm.uid=%s order by chatm.chatdate asc, chats.msgid asc"
    cursor.execute(s,[lid,uid])
    rs=cursor.fetchall()
    alist=[]
    for r in rs:
        x={'chatid':r[0],'chatdate':r[3],'msg':r[5],'typ':r[6]}
        alist.append(x)
    patname=uid
    s2="select uname from user where uid=%s"
    cursor.execute(s2,[uid])
    rp=cursor.fetchone()
    if rp:
        patname=rp[0]
    return render(request,'dchat.html',{'uid':uid,'lid':lid,'alist':alist,'patname':patname})

@require_role('doctor')
def dchataction(request):
    cursor=connection.cursor()
    lid=request.session['uid']
    uid=request.POST['uid']
    msg=request.POST['msg']
    ss="select chatid from chatm where uid=%s and lid=%s and chatdate=%s"
    cursor.execute(ss,[uid,lid,today])
    row=cursor.fetchone()
    if row:
        chid=row[0]
    else:
        sql1="insert into chatm(lid,uid,chatdate) values(%s,%s,%s)"
        cursor.execute(sql1,[lid,uid,today])
        chid=cursor.lastrowid
    sql="insert into chats(chatid,msg,typ)values(%s,%s,'doctor')"
    cursor.execute(sql,[chid,msg])
    msg="<script>;window.location='/dchat?uid="+uid+"';</script>"
    return HttpResponse(msg)
    

from datetime import date   # ✅ Add this import

@require_role('user')
def givefeedback(request):
    if request.method == "POST":
        cursor = connection.cursor()
        uid = request.session['uid']  # logged-in user id
        feedback = request.POST['feedback']
        fdate = date.today()

        sql = "INSERT INTO feedback(uid, feedback, fdate) VALUES (%s,%s,%s)"
        cursor.execute(sql, [uid, feedback, fdate])
        return HttpResponse("<script>alert('Feedback submitted successfully');window.location='/viewfeedback/';</script>")

    return render(request, "givefeedback.html")



# View all feedbacks (of that user or all users)
@require_role('user')
def viewfeedback(request):
    cursor = connection.cursor()
    uid = request.session['uid']
    sql = "SELECT fid, feedback, fdate FROM feedback WHERE uid=%s"
    cursor.execute(sql, [uid])
    rs = cursor.fetchall()
    fb = []
    for row in rs:
        q = {'fid': row[0], 'feedback': row[1], 'fdate': row[2]}
        fb.append(q)
    return render(request, "viewfeedback.html", {"fb": fb})


@require_role('admin')
def admin_viewfeedback(request):
    cursor = connection.cursor()
    sql = """
        SELECT f.fid, u.uname, f.feedback, f.fdate
        FROM feedback f
        JOIN user u ON f.uid = u.uid
        ORDER BY f.fdate DESC
    """
    cursor.execute(sql)
    rs = cursor.fetchall()
    fb = []
    for row in rs:
        q = {
            'fid': row[0],
            'uname': row[1],
            'feedback': row[2],
            'fdate': row[3]
        }
        fb.append(q)
    return render(request, "admin_viewfeedback.html", {"fb": fb})


NEWS_ARTICLES = {
    '1': {
        'id': '1',
        'icon': 'bi-journal-medical',
        'category': 'Pharmacology',
        'title': 'Recent FDA Drug Approvals',
        'date': 'March 15, 2024',
        'excerpt': 'Discover the latest medications approved by regulatory agencies and their applications in modern healthcare.',
        'body': [
            'Regulatory agencies continually review and approve new medications aimed at treating a wide range of conditions, from chronic illnesses to rare diseases. Staying informed about these approvals helps patients and caregivers understand new treatment options as they become available.',
            'Newly approved drugs typically undergo years of clinical trials to establish safety and efficacy before reaching pharmacy shelves. Once approved, healthcare providers assess how these medications fit into existing treatment plans.',
            'Patients are encouraged to speak with their doctor or pharmacist about whether a newly approved medication might be a suitable alternative or addition to their current regimen.',
        ],
    },
    '2': {
        'id': '2',
        'icon': 'bi-shield-exclamation',
        'category': 'Safety',
        'title': 'Drug Interaction Guide',
        'date': 'March 12, 2024',
        'excerpt': 'Understanding drug interactions is crucial for safe medication management. Learn what combinations to avoid.',
        'body': [
            'Drug interactions occur when one medication affects how another works, which can reduce effectiveness or increase the risk of side effects. Interactions can happen between prescription drugs, over-the-counter medicines, supplements, and even certain foods.',
            'Common warning signs of a harmful interaction include unusual drowsiness, upset stomach, or a sudden change in how a condition is being managed. Always keep an updated list of everything you take, including vitamins and herbal supplements.',
            'Pharmacists are a valuable resource for checking potential interactions before starting a new medication, and most pharmacy systems automatically flag known risky combinations.',
        ],
    },
    '3': {
        'id': '3',
        'icon': 'bi-heart-fill',
        'category': 'Treatment',
        'title': 'Managing Chronic Diseases',
        'date': 'March 10, 2024',
        'excerpt': 'Effective medication strategies for long-term disease management and improved quality of life.',
        'body': [
            'Living with a chronic condition such as diabetes, hypertension, or asthma often means managing a long-term medication routine alongside lifestyle changes. Consistency is one of the most important factors in keeping symptoms under control.',
            'Setting reminders, using pill organizers, and scheduling regular check-ins with a healthcare provider can help patients stay on track with their treatment plans.',
            'Long-term management works best as a partnership between the patient and their care team, with open communication about what is and is not working.',
        ],
    },
    '4': {
        'id': '4',
        'icon': 'bi-alarm-fill',
        'category': 'Wellness',
        'title': 'Improving Medication Adherence',
        'date': 'March 08, 2024',
        'excerpt': 'Tips and strategies to help patients stick to their medication regimens for better health outcomes.',
        'body': [
            'Medication adherence, or taking medicine exactly as prescribed, is one of the biggest factors in treatment success. Missed doses or early discontinuation can lead to setbacks in managing a condition.',
            'Simple strategies like linking doses to daily habits, using a weekly pill box, or setting phone alarms can make a noticeable difference in staying consistent.',
            'If side effects or cost are making it hard to stick to a regimen, patients should talk to their provider rather than stopping treatment on their own.',
        ],
    },
    '5': {
        'id': '5',
        'icon': 'bi-book-half',
        'category': 'Education',
        'title': 'Generic vs Brand Name Drugs',
        'date': 'March 05, 2024',
        'excerpt': 'Understanding the differences, similarities, and cost implications of generic and brand-name medications.',
        'body': [
            'Generic medications contain the same active ingredients as their brand-name counterparts and must meet the same standards for quality, strength, and safety.',
            'The main difference is usually cost: generics are often significantly cheaper because manufacturers do not need to repeat the original clinical trials or cover the same marketing costs.',
            'For most patients, switching to a generic version has no impact on treatment effectiveness, though it is always reasonable to ask a pharmacist if there are any specific concerns.',
        ],
    },
    '6': {
        'id': '6',
        'icon': 'bi-thermometer-half',
        'category': 'Health',
        'title': 'Managing Medication Side Effects',
        'date': 'March 01, 2024',
        'excerpt': 'Learn how to identify, prevent, and manage common side effects from your medications safely.',
        'body': [
            'Most medications carry some risk of side effects, ranging from mild and temporary to more serious reactions that require medical attention.',
            'Reading the information leaflet that comes with a prescription and knowing what symptoms to watch for can help patients respond quickly if something feels wrong.',
            'Any severe or unexpected reaction should be reported to a healthcare provider right away, while milder side effects can often be discussed at the next regular appointment.',
        ],
    },
}


def newsdetail(request):
    nid = request.GET.get('id', '1')
    article = NEWS_ARTICLES.get(nid)
    return render(request, "newsdetail.html", {"article": article})
