<div id="side">
	<p class="bio">
		<img src="{{ get_url('static', path='assets/img/avatar-small.png') }}" />{{username}}
	</p>
	<div>
	<ul class="follow">
            %for lusername in userlist:
	        <li><strong><a href="/{{lusername}}">{{lusername}}</a></strong></li>
            %end

	</ul>
</div>