%#user's profile page
%include shared/header.tpl header=page,logged=logged
<div id="main">
	<img src="/static/assets/img/avatar.png" float="right"/>
	<h1>{{username}}</h1>
	<p>Here's some information about you.</p>
	<div id="snippet-button", width=400, height=200, background-color="red">
		<p>View {{username}}'s code.</p>
	</div>
</div>
%#include shared/side.tpl username=username,userlist=userlist
	
%include shared/footer.tpl