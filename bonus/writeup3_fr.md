# Boot in Root

Apres quelques recherche, on se rend compte que ll'une des methodes les plus simples pour devenir est de passer par **grub** pour nous mettre dans un mode **"Recovery"**.

Cependant nous n'avons pas grub.

Il s'avere que l'ISO possède **syslinux**

On cherche le fichier de config de syslinux (**isolinux.cfg**), donc :
<pre><code>> find / -type f -name isolinux.cfg -print 2>/dev/null
/cdrom/isolinux/isolinux.cfg
> cat /cdrom/isolinux/isolinux.cfg
default live
prompt 0
timeout 0

menu title BornToSec
menu background splash.png
menu color title 1;37;44 #c0ffffff #00000000 std

label live
  menu label live - boot the Live System
  kernel /casper/vmlinuz
  append  file=/cdrom/preseed/custom.seed boot=casper initrd=/casper/initrd.gz quiet splash --
</code></pre>

Donc on sait que pour boot, notre ISO utilise le *label* **live**.

On relance notre VM en maintenant appuyée la touche [Shift] ou [Alt] pour esquiver le lancement par defaut (defini par **isolinux.cfg**).

Une fois dans le terminal "**Recovery**" on tape la commande suivante:
<pre><code>live init=/bin/sh</code></pre>
> On utlise le label live pour boot normalement et on y ajoute la commande <code>init=/bin/sh</code>, ce qui va obliger le kernel a éxécuter /bin/sh au lieu de sont init par défaut.


![Root to Boot](writeup3.png "Screenshot")