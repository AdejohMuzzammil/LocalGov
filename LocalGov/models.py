from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

from django.contrib.auth.models import User


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('chairman', 'Chairman'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=20)

    def __str__(self):
        return self.user.username

class State(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class LocalGovernment(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, related_name='local_governments', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ChairmanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    # Updated related_name attributes to avoid clashes
    state = models.ForeignKey(State, related_name='chairman_profiles', on_delete=models.CASCADE)
    local_government = models.ForeignKey(LocalGovernment, related_name='chairman_profiles', on_delete=models.CASCADE)
    tenure_start_date = models.DateField(blank=True, null=True)
    tenure_end_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField()

    def __str__(self):
        return self.user.username
    

class Post(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='media/post_images/', blank=True, null=True)
    video = models.FileField(upload_to='media/post_videos/', blank=True, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey(State, related_name='post_states', on_delete=models.CASCADE)
    local_government = models.ForeignKey(LocalGovernment, related_name='post_local_governments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    def __str__(self):
        return self.title

    

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)  
    like_count = models.ManyToManyField(User, related_name='liked_comments', blank=True)  
    dislike_count = models.ManyToManyField(User, related_name='disliked_comments', blank=True)  

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'


# migrations/0002_populate_states.py
from django.db import migrations

def populate_states(apps, schema_editor):
    State = apps.get_model('LocalGov', 'State')
    LocalGovernment = apps.get_model('LocalGov', 'LocalGovernment')

    states_and_lgas = {
        "Abia": ["Aba North", "Aba South", "Arochukwu", "Bende", "Isiala Ngwa North", "Isiala Ngwa South", "Isuikwuato", "Obingwa", "Ohafia", "Osisioma", "Ugwunagbo", "Ukwa East", "Ukwa West", "Umuahia North", "Umuahia South"],
        "Adamawa": ["Demsa", "Fufore", "Ganye", "Girei", "Guyuk", "Hong", "Jada", "Lamurde", "Mubi North", "Mubi South", "Numan", "Shelleng", "Song", "Yola North", "Yola South"],
        "Akwa Ibom": ["Abak", "Ekpenyong", "Essien Udim", "Etim Ekpo", "Etinan", "Ibiono Ibom", "Ibesikpo Asutan", "Ikono", "Ikot Abasi", "Ikot Ekpene", "Ini", "Mbo", "Mkpat Enin", "Nsit Atai", "Nsit Ibom", "Obot Akara", "Okobo", "Onna", "Oron", "Oruk Anam", "Uyo"],
        "Anambra": ["Aguata", "Anambra East", "Anambra West", "Dunukofia", "Ekwusigo", "Idemili North", "Idemili South", "Ihiala", "Njikoka", "Nnewi North", "Nnewi South", "Ogbaru", "Onitsha North", "Onitsha South", "Orumba North", "Orumba South", "Oyi"],
        "Bauchi": ["Alkaleri", "Bauchi", "Bogoro", "Dambam", "Darazo", "Ganjuwa", "Gamawa", "Jos East", "Jos North", "Kirfi", "Misau", "Ningi", "Shira", "Tafawa Balewa", "Toro", "Warji", "Zaki"],
        "Bayelsa": ["Brass", "Ekeremor", "Kolokuma/Opokuma", "Nembe", "Ogbia", "Sagbama", "Southern Ijaw", "Yenagoa"],
        "Benue": ["Ado", "Agatu", "Apa", "Buruku", "Gboko", "Guma", "Gwer East", "Gwer West", "Katsina-Ala", "Konshisha", "Logo", "Makurdi", "Obi", "Ogbadibo", "Ohimini", "Oturkpo", "Tarka", "Vandeikya"],
        "Borno": ["Abadam", "Askira/Uba", "Bama", "Bayo", "Biu", "Chibok", "Damboa", "Dikwa", "Gubio", "Guzamala", "Hawul", "Kaga", "Kwaya Kusar", "Mafa", "Magumeri", "Maiduguri", "Monguno", "Ngala", "Nganzai", "Shani"],
        "Cross River": ["Akamkpa", "Bakassi", "Biase", "Boki", "Calabar Municipal", "Calabar South", "Duke", "Ikom", "Obanliku", "Obubra", "Odukpani", "Ogoja", "Yakuur", "Yala"],
        "Delta": ["Aniocha North", "Aniocha South", "Asaba", "Bomadi", "Burutu", "Ethiope East", "Ethiope West", "Ika North East", "Ika South", "Isoko North", "Isoko South", "Ndokwa East", "Ndokwa West", "Okpe", "Oshimili North", "Oshimili South", "Patani", "Sapele", "Udu", "Ughelli North", "Ughelli South", "Warri North", "Warri South", "Warri South-West"],
        "Ebonyi": ["Abakaliki", "Afikpo North", "Afikpo South", "Ebonyi", "Ishielu", "Ivo", "Ohaozara", "Onicha", "Ohaukwu", "Ezza North", "Ezza South"],
        "Edo": ["Akoko-Edo", "Esan Central", "Esan North-East", "Esan South-East", "Egor", "Igueben", "Ikpoba-Okha", "Oredo", "Ovia North-East", "Ovia South-West", "Uhunmwonde"],
        "Ekiti": ["Ado Ekiti", "Ekiti East", "Ekiti South-West", "Ekiti West", "Emure", "Ido Osi", "Ijero", "Ikere", "Ikole", "Oye"],
        "Enugu": ["Awgu", "Enugu East", "Enugu North", "Enugu South", "Igbo Eze North", "Igbo Eze South", "Isi Uzo", "Nkanu East", "Nkanu West", "Oji River", "Udi", "Uzo Uwani"],
        "Gombe": ["Akko", "Balanga", "Billiri", "Dukku", "Gombe", "Kaltungo", "Kwami", "Nafada", "Shongom", "Yamaltu/Deba"],
        "Imo": ["Aboh Mbaise", "Ahiazu Mbaise", "Ehime Mbano", "Ikeduru", "Isiala Mbano", "Isu", "Mbaitoli", "Ngor Okpala", "Njaba", "Nkwere", "Obowo", "Oguta", "Ohaji/Egbema", "Okigwe", "Orlu", "Orsu", "Owerri Municipal", "Owerri North", "Owerri West"],
        "Jigawa": ["Auyo", "Babura", "Birnin Kudu", "Dutse", "Gwaram", "Gwiwa", "Hadejia", "Jahun", "Kafin Hausa", "Kazaure", "Kiri Kasama", "Maigatari", "Malam Madori", "Miga", "Ringim", "Sule Tankarkar", "Yankwashi"],
        "Kaduna": ["Birnin Gwari", "Chikun", "Giwa", "Igabi", "Jaba", "Jema'a", "Kachia", "Kaduna North", "Kaduna South", "Kagarko", "Kaura", "Kauru", "Lere", "Sanga", "Zango Kataf"],
        "Kano": ["Ajingi", "Albasu", "Bagwai", "Bebeji", "Bichi", "Bunkure", "Dala", "Dawakin Kudu", "Dawakin Tofa", "Doguwa", "Fagge", "Gaya", "Gezawa", "Gwarzo", "Kano Municipal", "Karaye", "Kibiya", "Kiru", "Madobi", "Minjibir", "Nasarawa", "Rogo", "Shanono", "Sumaila", "Tofa", "Tudun Wada", "Wudil"],
        "Kogi": ["Adavi", "Ajaokuta", "Ankpa", "Bassa", "Dekina", "Ibaji", "Idah", "Igalamela Odolu", "Ogori/Magongo", "Okehi", "Okene", "Olamaboro", "Omala", "Yagba East", "Yagba West"],
        "Kwara": ["Asa", "Baruten", "Ekiti", "Ifelodun", "Ilorin East", "Ilorin South", "Ilorin West", "Irepodun", "Isin", "Kaiama", "Offa", "Oyun"],
        "Lagos": ["Agege", "Ajeromi-Ifelodun", "Alimosho", "Apapa", "Badagry", "Epe", "Eti-Osa", "Ibeju-Lekki", "Ifako-Ijaiye", "Ikorodu", "Lagos Island", "Lagos Mainland", "Mushin", "Ojo", "Oshodi-Isolo", "Somolu", "Surulere"],
        "Nasarawa": ["Akwanga", "Assakio", "Doma", "Karu", "Keffi", "Kokona", "Nasarawa", "Nasarawa Eggon", "Obi", "Toto"],
        "Niger": ["Agaie", "Agwara", "Bida", "Borgu", "Bosso", "Chanchaga", "Edati", "Gurara", "Katcha", "Lavun", "Lapai", "Minna", "Moro", "Paikoro", "Rafi", "Shiroro"],
        "Ogun": ["Abeokuta North", "Abeokuta South", "Ado-Odo/Ota", "Egbado North", "Egbado South", "Ewekoro", "Ifo", "Ijebu East", "Ijebu North", "Ijebu North East", "Ijebu Ode", "Obafemi-Owode", "Ogun Waterside", "Remo North", "Sagamu", "Yewa North", "Yewa South"],
        "Ondo": ["Akoko North-East", "Akoko North-West", "Akoko South-East", "Akoko South-West", "Akure North", "Akure South", "Ese-Odo", "Idanre", "Ifedore", "Ilaje", "Odigbo", "Owo"],
        "Osun": ["Atakunmosa East", "Atakunmosa West", "Ayedaade", "Ayedire", "Boluwaduro", "Boripe", "Ife Central", "Ife East", "Ife North", "Ife South", "Ilesa East", "Ilesa West", "Irepodun", "Isokan", "Obokun", "Odo-Otin", "Oluyole", "Oshogbo"],
        "Oyo": ["Akinyele", "Atiba", "Ayeye", "Bodija", "Egbeda", "Ibadan North", "Ibadan North East", "Ibadan South East", "Ibadan South West", "Ibarapa Central", "Ibarapa East", "Ibarapa North", "Ido", "Iseyin", "Itesiwaju", "Ogbomosho North", "Ogbomosho South", "Oyo East", "Oyo West", "Saki East", "Saki West"],
        "Plateau": ["Barkin Ladi", "Bassa", "Bokkos", "Jos East", "Jos North", "Kanam", "Kanke", "Langtang North", "Langtang South", "Mangu", "Pankshin", "Qua'an Pan", "Riyom", "Shendam", "Wase"],
        "Rivers": ["Abua/Odual", "Ahoada East", "Ahoada West", "Akuku-Toru", "Andoni", "Asari-Toru", "Bonny", "Degema", "Eleme", "Emuoha", "Etche", "Gokana", "Ikwerre", "Obio-Akpor", "Ogu/Bolo", "Ogba/Egbema/Ndoni", "Okrika", "Omuma", "Port Harcourt", "Tai"],
        "Sokoto": ["Aleiro", "Babber Ruga", "Bagudo", "Bodinga", "Dange Shuni", "Gada", "Goronyo", "Gudu", "Illela", "Kebbe", "Kware", "Rabah", "Sabon Birni", "Shagari", "Sokoto North", "Sokoto South", "Wammako"],
        "Taraba": ["Ardo Kola", "Donga", "Gashaka", "Gassol", "Jalingo", "Karim Lamido", "Kumi", "Lau", "Sardauna", "Takum", "Ussa", "Wukari"],
        "Yobe": ["Bade", "Bursari", "Damaturu", "Fika", "Fune", "Geidam", "Gujba", "Gashua", "Nguru", "Potiskum", "Tarmuwa", "Yunusari", "Yobe"],
        "Zamfara": ["Anka", "Bakura", "Birnin Magaji", "Bukkuyum", "Chafe", "Gummi", "Isa", "Kaura Namoda", "Maradun", "Shinkafi", "Talata Mafara", "Zamfara"],
    }

    for state_name, lgas in states_and_lgas.items():
        state = State.objects.create(name=state_name)
        for lga_name in lgas:
            LocalGovernment.objects.create(name=lga_name, state=state)

class Migration(migrations.Migration):
    dependencies = [
        ('LocalGov', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_states),
    ]
