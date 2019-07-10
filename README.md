<h4><b>Install Python at https://www.python.org/downloads/release/python-371/</b></h4>
<h4><b>Install Pillow Library at https://pypi.org/project/Pillow/ </b></h4>
<h4><b>Compatible with Shovel Knight PC versions only</b></h4>

*Make sure to make copies of your files!

<section>
<h5>The .pak Packer Tool</h5>
<p>To unpack a .pak file using pack_packer simply drag/drop the .pak file onto pack_packer.py</p>
<p>To repack the unpacked folder, simply drag/drop the generatd folder onto pack_packer.py</p>
</section>
<section>
<h5>The .anb Packer Tool</h5>
<p>To unpack a .anb file simply drag/drop the .anb file onto anb_packer.py</p>
<p>To repack the extracted images simply drag/drop the folder where the images are located onto anb_packer.py</p>
</section>

<h3>Sprite Editing Instructions</h3>
<ol>
  <li>Unpack the target .pak file</li>
  <li>Unpack the target .anb file</li>
  <li>Edit the extracted images</li>
  <li>Repack the folder where the edited images are using ANB_PACKER</li>
  <li>Replace the original .ANB with your modded.anb file</li>
  <li>Repack the folder using PAK_PACKER</li>
  <li>Replace the original .pak file with your modded .pak</li>
  <li>Profit.</li>
</ol>

**Warnings**
<p>Do not resize the images.</p>
<p>Do not rename the images.</p>
<p>Images must be in RGBA PNG format.</p>
<p>You don't need to edit all the images, the tools will simply repack the unedited images along with yours.</p>
<p>The meta.dat file contains repacking information, make sure is always with the images.</p>

**Tips**
The .pak packer tool skips any extra files it finds in the folder and keeps track of what files must be present when repacking.
It also only changes the files you edit, thus saving time when repacking.

The .anb tool works the same way.

<h2>Happy Modding!</h2>
<img src = "http://yachtclubgames.com/wp-content/uploads/2015/02/plagueKnight0031.png" width = "164" height = "164">
<img src = "https://i.postimg.cc/hvjzLWJk/Untitled.png" width="400" height = "300">
