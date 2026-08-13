var nm=require("nodemailer")
var trans=nm.createTransport({host:"smtp.gmail.com",port:465,
    auth:{user:"vrushtipatel545@gmail.com",
        pass:"kcpf tbsl klul wrgb"
    }
})
var mailoptions={
    from:"noreply@gmail.com",
    to:"vrushtipatel545@gamil.com",
    subject:"Nodemailer Example",
    text:"Testmg mail",
    html:"<h1>Successful Testmg</h1><h3>Thank you!</h3>",
    attachments:[{filename:"1.png.jpg",path:"./1.png.jpg"}]
}
trans.sendMail(mailoptions,(e,d)=>{
    if(e){
        console.log(e)
    }
    else{
        console.log(d)
    }
})