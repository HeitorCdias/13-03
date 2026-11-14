// Unidades em mm. Exemplo, conferir dimensões reais antes de fabricar.
// Não é peça estrutural certificada nem recomendação para imprimir a moldura.
// Abra no OpenSCAD. part: assembly, front, body, back, front2d.
part = "assembly";
monitor_w = 310; monitor_h = 530; monitor_d = 45;
clearance = 8; rail = 40; lip = 12;
front_t = 18; wall = 18; body_d = 92; back_t = 6;
glass_t = 4; rebate_d = 6;
opening_w = monitor_w + 2*clearance;
opening_h = monitor_h + 2*clearance;
outer_w = opening_w + 2*rail;
outer_h = opening_h + 2*rail;
glass_w = opening_w + 2*lip - 2;
glass_h = opening_h + 2*lip - 2;
$fn=48;
module front(){
  difference(){
    translate([-outer_w/2,-outer_h/2,0])cube([outer_w,outer_h,front_t]);
    translate([-opening_w/2,-opening_h/2,-1])cube([opening_w,opening_h,front_t+2]);
    translate([-(opening_w+2*lip)/2,-(opening_h+2*lip)/2,front_t-rebate_d])cube([opening_w+2*lip,opening_h+2*lip,rebate_d+1]);
    // Furos-guia: ajustar ao módulo e à lente antes de cortar.
    translate([0,outer_h/2-rail/2,-1])cylinder(h=front_t+2,d=10);
    translate([-45,-outer_h/2+rail/2,-1])cylinder(h=front_t+2,d=23);
    translate([0,-outer_h/2+rail/2,-1])cylinder(h=front_t+2,d=6);
  }
}
module body(){
  difference(){
    translate([-outer_w/2,-outer_h/2,0])cube([outer_w,outer_h,body_d]);
    translate([-outer_w/2+wall,-outer_h/2+wall,-1])cube([outer_w-2*wall,outer_h-2*wall,body_d+2]);
    // Aberturas nas paredes inferior e superior; acabamento com tela de proteção.
    for(y=[-outer_h/2-1,outer_h/2-wall-1])
      for(x=[-120:30:120])translate([x-6,y,35])cube([12,wall+2,40]);
  }
}
module back(){
  difference(){
    translate([-outer_w/2,-outer_h/2,0])cube([outer_w,outer_h,back_t]);
    translate([-30,-outer_h/2+30,-1])cube([60,18,back_t+2]); // passagem de cabos com prensa-cabo/borda
    for(x=[-outer_w/2+wall/2,outer_w/2-wall/2])
      for(y=[-outer_h/2+wall/2,outer_h/2-wall/2])translate([x,y,-1])cylinder(h=back_t+2,d=4);
  }
}
if(part=="front")front();
else if(part=="front2d")projection(cut=false)front();
else if(part=="body")body();
else if(part=="back")back();
else {
  color([.15,.18,.15])front();
  color([.5,.8,.9,.22])translate([-glass_w/2,-glass_h/2,front_t-rebate_d+.5])cube([glass_w,glass_h,glass_t]);
  color([.09,.09,.09])translate([-monitor_w/2,-monitor_h/2,front_t+12])cube([monitor_w,monitor_h,monitor_d]);
  color([.35,.25,.15,.35])translate([0,0,front_t])body();
  color([.2,.2,.2,.4])translate([0,0,front_t+body_d+12])back();
}
