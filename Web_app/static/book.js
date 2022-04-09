function filter(){
        var a=document.getElementById("exampleFormControlSelect1").value;
        var b=document.getElementById("selectcity");
        for(var i=b.options.length-1;i>=0;i--){
                b.remove(i);
             }
             if(a=="Moldova"){
                var option = document.createElement('option');
                option.text = "Chisinau";
                option.value="Chisinau";
                b.add(option);
            }
            if(a=="Romania"){
                var option = document.createElement('option');
                option.text = "Bucharest";
                option.value = "Bucharest";
                b.add(option);
                option = document.createElement('option');
                option.text = "Cluj-Napoca";
                option.value = "Cluj-Napoca";
                b.add(option);

            }
            if(a=="Turkey"){
                var option = document.createElement('option');
                option.text = "Ankara";
                option.value = "Ankara";
                b.add(option);
                option = document.createElement('option');
                option.text = "Istanbul";
                option.value = "Istanbul";
                b.add(option);

            }
        }