$(document).on("click", '.nav-item', function(){
  var current = this.id;
  console.log(current);
  get_mes(current);
});


$(document).ready(function() {

  namespace = '/test';
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
  console.log("---------");
  console.log(location.protocol + '//' + document.domain + ':' + location.port + namespace);
  console.log("---------");

  socket.on('connect', function() {
    socket.emit('want_connect', {data: 'I want to connect' });
  });

  socket.on('connected', function(msg) {
    //console.log('Hello. This is socketio');
    //console.log(socket);
    console.log(msg);
  });


  socket.on('print_my_send', function(msg) {
    //console.log(msg);
    //console.log(msg.id);
    console.log("print_my_send");
    var link = "#test" + msg.id + "for_text";
    var update_mess;
    var div_mess="<div class='d-flex justify-content-end mb-4'> <div class='msg_cotainer_send'>";
    var div_end="</div>";
    var span_time="<span class='msg_time_send'>";
    var span_hide="<span class='msg_origin_send'>";
    var span_end="</span>";
    update_mess = div_mess + msg.username + ":" + msg.content + span_hide + msg.hide + span_end + div_end + span_time + msg.time + span_end + div_end;
    //$(link).append( correspondence ).css("width", "50%");
    $(link).append( update_mess );
  });


  socket.on('print_to_me', function(msg) {
    console.log("print_to_me");
    var link = "#test" + msg.id + "for_text";
    var update_mess;
    var div_mess="<div class='d-flex justify-content-start mb-4'> <div class='msg_cotainer'>";
    var div_end="</div>";
    var span_time="<span class='msg_time'>";
    var span_hide="<span class='msg_origin'>";
    var span_end="</span>";
    update_mess = div_mess + msg.username+":" + msg.content + span_hide + msg.hide + span_end + div_end + span_time + msg.time + span_end + div_end;
    //$(link).append( correspondence ).css("width", "50%");
    $(link).append( update_mess );

  });


  $('.inputClass').each(function() {
    $(this).click(function(){
      var id = $(this).attr('id');
      //console.log(id);
      var mode_id="#" + id + 2;
      //console.log(mode_id);
      var data = $(mode_id).val();
      //console.log(id);
      //console.log(data);
      //send_mes(id,data);
      socket.emit('send_message', {content: data,to_id:id});
      //id=id.replace("send", '');
      //console.log(id);
      //get_mes(id);
    });
  });

  $(document).on("mouseenter", ".msg_cotainer", function () {
    //console.log('mouseenter');
    //console.log($(this).find("span"));
    $(this).find("span").css("display","block").show();
  });
  $(document).on("mouseenter", ".msg_cotainer_send", function () {
    //console.log('mouseenter');
    //console.log($(this).find("span"));
    $(this).find("span").css("display","block").show();
  });
  $(document).on("mouseleave", ".msg_cotainer", function () {
    //console.log('mouseleave');
    //console.log($(this).find("span"));
    $(this).find("span").hide();
  });
  $(document).on("mouseleave", ".msg_cotainer_send", function () {
    //console.log('mouseleave 2');
    //console.log($(this).find("span"));
    $(this).find("span").hide();
  });

});

function send_mes(ids,datas) {
    console.log(ids);
    $.post('/send_message', {
        message:datas ,
        id_to: ids
    }).done(function(response) {
        var iter=response['time'];
        //get_mes(ids);
        //alert(iter);
        var link;
        var correspondence;
        var pre="<div class='d-flex justify-content-start mb-4'> <div class='msg_cotainer'>";
        var ends="</div>";
        var pre2="<div class='d-flex justify-content-end mb-4'> <div class='msg_cotainer_send'>";
        var time="<span class='msg_time'>";
        var time2="<span class='msg_time_send'>";
        var hides="<span class='msg_origin'>";
        var hides2="<span class='msg_origin_send'>";
        var hides_end="</span>"
        var time_end="</span>";
        ids=ids.replace("send", ' ');
        link = "#test" + response['id_to'] + "for_text" ;
        console.log(link);
        console.log(response['time']);
        correspondence=pre2+ids+ ": " +datas+hides2+"This is origin language" + hides_end+ends+ time2+ response['time'] + time_end + ends;  
        $(link).append( correspondence ).css("width", "50%"); 
    }).fail(function() {
        console.log("error with send!");
    });
}


function get_mes(id_from) {
    $.post('/get_message', {
        id_2: id_from
    }).done(function(response) {
        //console.log(response['count_message'])
        var iter=response['count_message'];
        if(iter==0){
            var link = "#test" + id_from + "for_text";
            $(link).html("No messages in this chats").css("width", "30%");;
        } else {
            var i;
            var link;
            var correspondence;
            var pre="<div class='d-flex justify-content-start mb-4'> <div class='msg_cotainer'>";
            var ends="</div>";
            var pre2="<div class='d-flex justify-content-end mb-4'> <div class='msg_cotainer_send'>";
            var time="<span class='msg_time'>";
            var time2="<span class='msg_time_send'>";
            var hides="<span class='msg_origin'>";
            var hides2="<span class='msg_origin_send'>";
            var hides_end="</span>"
            var time_end="</span>";
            
            for (i=0;i<iter;i++) {
                /*!!!!!!!!КАК ПРИНТАНУТЬ В КОНСОЛЬ content каждого сообщения!!!!*/
                //console.log(response['messages'][i]['content'] );
                link = "#test" + id_from + "for_text" ;
                //console.log(link);
                //console.log(id_from);
                //console.log(response['messages'][i]['time']);
                if (i==0) {
                    if (id_from==response['messages'][i]['id']){
                        correspondence=pre+response['messages'][i]['username'] + ": " +response['messages'][i]['content']  +hides+response['messages'][i]['hide'] + hides_end +ends+time+response['messages'][i]['time'] + time_end+ ends;
                    }
                    else{
                        correspondence=pre2+response['messages'][i]['username'] + ": " +response['messages'][i]['content']+hides2+response['messages'][i]['hide'] + hides_end+ends+ time2+response['messages'][i]['time'] + time_end + ends; 
                    }
                } else {
                    if (id_from==response['messages'][i]['id']){
                        correspondence =  correspondence + pre+ response['messages'][i]['username'] + ": " +response['messages'][i]['content']+hides+response['messages'][i]['hide'] + hides_end+ends+ time+response['messages'][i]['time'] + time_end + ends;
                    }
                    else{
                        correspondence =  correspondence + pre2+ response['messages'][i]['username'] + ": " +response['messages'][i]['content']+hides2+response['messages'][i]['hide'] + hides_end+ ends+time2+response['messages'][i]['time'] + time_end + ends;
                    }
                }
                /*correspondence=response['messages'][i]['username'] + ": " +response['messages'][i]['content'] + "<br>";
                if( {{ current_user.username }} == response['messages'][i]['username'] ){
                  //correspondence=response['messages'][i]['username'] + ": " +response['messages'][i]['content'] + "<br>
                  $(link).append( correspondence ).css("width", "30%","color","#FFFF00");
                }
                else{
                 $(link).append( correspondence ).css("width", "30%","color","#2F4F4F");
                }*/

            }
            
            //$(link).html(correspondence);
            $(link).html(correspondence).css("width", "50%");
            // $(link).append( "<p style='color:#2F4F4F; background:#FFFF00'>Test</p>" );*/
            /* 
            setInterval(function() {
            $.post('/update_message', {
              id_2: id_from
            }).done(function(response){
              var iter=response['count_message'];
              if(iter==0){
                    console.log("No upadte message!");
            } else {
               var link = "#test" + id_from + "for_text";
               var correspondence;
               var pre="<div class='d-flex justify-content-start mb-4'> <div class='msg_cotainer'>";
               var ends="</div>";
               var time="<span class='msg_time'>";
                               var hides="<span class='msg_origin'>";
                               var hides_end="</span>"
                               var time_end="</span>";
               var i;
               for (i=0;i<iter;i++){
                if (i==0){
               correspondence=pre+response['messages'][i]['username'] + ": " +response['messages'][i]['content']  +hides+response['messages'][i]['hide'] + hides_end +ends+time+response['messages'][i]['time'] + time_end+ ends;
               }
               else{
                 correspondence =  correspondence + pre+ response['messages'][i]['username'] + ": " +response['messages'][i]['content']+hides+response['messages'][i]['hide'] + hides_end+ends+ time+response['messages'][i]['time'] + time_end + ends;
               }
               }
               $(link).append( correspondence ).css("width", "50%");
            }});
            }, 5000);
            */
           
        }
    }).fail(function() {
        console.log("ERROR!");
        var link = "#test" + id_from + "for_text" ;
        $(link).html("Error!").css("width", "50%");
    });
}
