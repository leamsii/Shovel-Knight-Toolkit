<h3>Dependencies</h3>
<h4><b>Install Python at https://www.python.org/downloads/release/python-371/</b></h4>
<h4><b>Install Pillow Library at https://pypi.org/project/Pillow/ </b></h4>
<h4><b>Compatible with Shovel Knight PC versions only</b></h4>

<h3>Sprite Editing Instructions</h3>
<b>!Make sure to make copies of your .PAK files!</b>

<ol>
  <li>Unpack the target .pak file</li>
  <li>Unpack the target .anb file</li>
  <li>Edit the extracted images</li>
  <li>Repack the folder where the edited images are using the ANB_TOOL</li>
  <li>Replace the original .anb file with your new .anb file (should be in your editted sprites folder)</li>
  <li>Repack the unpacked .pak folder using the pak_tool</li>
  <li>Replace the original .pak file with your modded .pak file, should be inside unpacked .pak folder</li>
</ol>

<h3> Warnings </h3>
<ul>
<li>DO NOT rename the images</li>
<li>Images must be in RGBA PNG format (Try Gimp)</li>
<li>You don't need to edit all the images, the tools will simply repack the unedited images along with yours</li>
<li>Don't delete any metadata files</li>
</ul>

<h3>How to Use The Tools</h3>
<section>
<h5>The .pak Packer Tool</h5>
  <p>To unpack a .pak file using the pak_tool, in CMD, while in ToolKit folder, run python pak_tool.py "FILE SOURCE"</p>
  <p>To re-pack a folder, run python pak_tool.py "FOLDER SOURCE"</p>
</section>
 
<section>
<h5>The .anb Packer Tool</h5>
  <p>To unpack an .anb file run python anb_tool.py "FILE SOURCE", in CMD, while in ToolKit folder</p>
  <p>To repack sprites run python anb_tool.py "FOLDER SOURCE"</p>
</section>

<h2>Happy Modding!</h2>
<img src = "https://i.postimg.cc/hvjzLWJk/Untitled.png" width="400" height = "300">
