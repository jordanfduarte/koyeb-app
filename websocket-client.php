<?php
header("Access-Control-Allow-Origin: *");
// MODE 1 = http://ws.achex.ca/ 2 = https://www.piesocket.com/
$MODE = 1;
$notSend = isset($_GET['notSend']);
require "./websocket-lib.php";

$arrUsersAllow = [
    'Jordan'    => '75f4afbe004f271539638bcbc7b15cb7', // Jordan
    'Adriana'   => '0113439137b812cb974bacaf5b71045b', // Adriana
    'Convidado' => '446c055e591ce907debee78e5f71b1fd' // Convidado
];
// error_log(print_r($_GET, true), 3, getcwd() . "/log.log");
if (!isset($_GET['token']) || !in_array($_GET['token'], $arrUsersAllow)) {
    exit;
}

$numerosEmIngles = [
    1 => 'one',
    2 => 'two',
    3 => 'three',
    4 => 'four',
    5 => 'five',
    6 => 'six',
    7 => 'seven',
    8 => 'eight',
    9 => 'nine'
];

foreach ($numerosEmIngles as $n => $numeroIngles) {
    if (isset($_GET['l' . $numeroIngles])) {
        $_GET['l' . $n] = $_GET['l' . $numeroIngles];
        unset($_GET['l' . $numeroIngles]);
    }
}

if (isset($_GET['comando'])) {
    switch($_GET['comando']) {
        case 'home':
            include "services.php"; exit;
        break;
        case 'one': $_GET['r'] = 1; break; // Ligar Radio
        case 'two': $_GET['r'] = 2; break; // Desligar Radio
        case 'radio': $_GET['r'] = 3; break; // Tunner Radio
        case 'four': $_GET['r'] = 4; break; // Aumentar volume do Radio
        case 'five': $_GET['r'] = 5; break; // Diminuir volume do Rádio
        case 'six': $_GET['r'] = 6; break; // Acvançar estação
        case 'seven': $_GET['r'] = 7; break; // Retroceder estação de Rádio

        case 'eight': $_GET['t'] = 1; break; // Ligar TV
        case 'nine': $_GET['t'] = 2; break; // AumentarVolumeTv
        case 'volume': $_GET['t'] = 3; break; // DiminuirVolumeTv
        case 'eleven': $_GET['t'] = 1; break; // DesligarTv

        case 'twelve': $_GET['c'] = 2; break; // ligarReceptor
        case 'thirteen': $_GET['c'] = 2; break; // desligarReceptor
        case 'fourteen': $_GET['c'] = 3; break; // aumentarVolumeReceptor
        case 'fifteen': $_GET['c'] = 4; break; // diminuirVolumeReceptor
        case 'sixteen': $_GET['c'] = 5; break; // proximoCanalReceptor
        case 'seventeen': $_GET['c'] = 6; break; // canalAnteriorReceptor
    }
}
$user = current(array_keys($arrUsersAllow, $_GET['token']));
if (isset($_GET['l5']) || isset($_GET['lfive'])) {
    $_GET['l1'] = 1;
    $_GET['l2'] = 1;
    $_GET['l3'] = 1;
    $_GET['l4'] = 1;
}

if (isset($_GET['01'])) {
    $_GET['l1'] = $_GET['01'];
    unset($_GET['01']);
}
if (isset($_GET['02'])) {
    $_GET['l2'] = $_GET['02'];
    unset($_GET['02']);
}
if (isset($_GET['03'])) {
    $_GET['l3'] = $_GET['03'];
    unset($_GET['03']);
}
if (isset($_GET['04'])) {
    $_GET['l4'] = $_GET['04'];
    unset($_GET['04']);
}
if (isset($_GET['06'])) {
    $_GET['l6'] = $_GET['06'];
    unset($_GET['06']);
}

if (isset($_GET['lsix'])) {
    $_GET['l6'] = $_GET['lsix'];
    unset($_GET['lsix']);
}

if (isset($_GET['0six'])) {
    $_GET['l6'] = $_GET['0six'];
    unset($_GET['0six']);
}

$getAllowed = ['l1', 'l2', 'l3', 'l4', 'l6',  'r', 't', 'c'];
foreach ($_GET as $h => $g) {
    if (!in_array($h, $getAllowed)) {
        unset($_GET[$h]);
    }
}


$command = http_build_query($_GET);
if ((isset($_GET['r']) || isset($_GET['t']) || isset($_GET['c'])) && !preg_match("/&/", $command)) {
    $command = "&" . $command;
}

$command = str_replace(["r", "t", "c", "l"], ["5", "6", "7", "0"], $command);

date_default_timezone_set('America/Sao_Paulo');
$dateNow = date('d/m/Y H:i');

$tentativas = 0;
$status = false;
if (!$notSend) {
    if ($MODE == 2) {
        $c = new WebSocketClient();
        $c->connect('ws://connect.websocket.in:80', '/v3/1?api_key=bo3B7OhgfkJXMtqNsvYw2zDWGqeiiTsC2FVq5qaL&notify_self');
        $c->send('{"to":"arduino@1107","value":"' . $command . '"}', 'text', true);

        while(true) {
            if ($tentativas == 3) {
                break;
            }


            $tentativas++;

            foreach ($r as $rr) {
                if (isset($rr['payload'])) {
                    $j = json_decode($rr['payload'], true);

                    if (isset($j['value']) && $j['value'] == "OK") {
                        $status = true;
                        break 2;
                    }
                }
            }
            $r = $c->recv();

            //var_dump($r);
        }
        $c->close();
    } else {
        $c = new WebSocketClient();
        $c->connect('ws://ws.achex.ca:4010');
        // $c->set_timeout(5);
        $c->send('{"setID":"jordan@1107","passwd":"142536"}', 'text', false);
        $r = $c->recv();
        if ($command == "&6=1") {
            //7=t213
            $command = "&6=1&6=3&7=t213&6=4";
        }
        $c->send('{"to":"arduino@1107","value":"' . $command . '"}', 'text', true);

        while(true) {
            if ($tentativas == 3) {
                // se ligar tv coloca no canala da globo
                if ($command == "&6=1" && false) {
                    $command = "&7=t213";
                    $c->send('{"to":"arduino@1107","value":"&7=t213"}', 'text', true);
                    //sleep(1000);
                    //$r = $c->recv();
                    //&6=4 // HDMI1
                    //$c->send('{"to":"arduino@1107","value":"&6=4"}', 'text', true);
                    //sleep(1000);
                    //$r = $c->recv();
                    //&6=3 // ABAIXAR VOLUME
                    //$c->send('{"to":"arduino@1107","value":"&6=3"}', 'text', true);
                    //sleep(1000);
                    //$r = $c->recv();
                    //break;
                } else {
                    break;
                }
            }

            if ($tentativas == 6) {
                break;
            }


            $tentativas++;

            foreach ($r as $rr) {
                if (isset($rr['payload'])) {
                    $j = json_decode($rr['payload'], true);

                    if (isset($j['value']) && $j['value'] == "OK") {
                        $status = true;
                        if ($tentativas < 3) {
                            if ($command == "&t=1" && false) {
                                $command = "&7=t213";
                                $c->send('{"to":"arduino@1107","value":"&7=t213"}', 'text', true);
                                //sleep(1);
                                //$r = $c->recv();
                                //&6=4 // HDMI1
                                //$c->send('{"to":"arduino@1107","value":"&6=4"}', 'text', true);
                                //sleep(1);
                                //$r = $c->recv();
                                //&6=3 // ABAIXAR VOLUME
                                //$c->send('{"to":"arduino@1107","value":"&6=3"}', 'text', true);
                                //sleep(1);
                                //$r = $c->recv();
                                //break 2;
                            } else {
                                break 2;
                            }
                        }
                        if ($tentativas > 3 && $command == "&7=t213") {
                            break 2;
                        }
                    }
                }
            }
            $r = $c->recv();

            //var_dump($r);
        }
        $c->close();
    }
} else {
    $status = true;
    $tentativas = 3;
}

$update = false;
$dataUpdate = [];
if (isset($_GET['l1'])) {
    if (!isset($dataUpdate['l1'])) {
        $dataUpdate['l1'] = [];
    }
    $dataUpdate['l1']['status'] = $_GET['l1'];
    $dataUpdate['l1']['data'] = $dateNow;
    $dataUpdate['l1']['user'] = $user;
    $update = true;
}

if (isset($_GET['l2'])) {
    if (!isset($dataUpdate['l2'])) {
        $dataUpdate['l2'] = [];
    }
    $dataUpdate['l2']['status'] = $_GET['l2'];
    $dataUpdate['l2']['data'] = $dateNow;
    $dataUpdate['l2']['user'] = $user;
    $update = true;
}

if (isset($_GET['l3'])) {
    if (!isset($dataUpdate['l3'])) {
        $dataUpdate['l3'] = [];
    }
    $dataUpdate['l3']['status'] = $_GET['l3'];
    $dataUpdate['l3']['data'] = $dateNow;
    $dataUpdate['l3']['user'] = $user;
    $update = true;
}

if (isset($_GET['l4'])) {
    if (!isset($dataUpdate['l4'])) {
        $dataUpdate['l4'] = [];
    }
    $dataUpdate['l4']['status'] = $_GET['l4'];
    $dataUpdate['l4']['data'] = $dateNow;
    $dataUpdate['l4']['user'] = $user;
    $update = true;
}

if (isset($_GET['l6'])) {
    if (!isset($dataUpdate['l6'])) {
        $dataUpdate['l6'] = [];
    }
    $dataUpdate['l6']['status'] = $_GET['l6'];
    $dataUpdate['l6']['data'] = $dateNow;
    $dataUpdate['l6']['user'] = $user;
    $update = true;
}

// Radio
if (isset($_GET['r'])) {
    if (!isset($dataUpdate['r'])) {
        $dataUpdate['r'] = [];
    }
    $dataUpdate['r'] = ['status' => $_GET['r'], 'data' => $dateNow, 'user' => $user];
    $update = true;
}

// RECEPTOR
if (isset($_GET['c'])) {
    if (!isset($dataUpdate['c'])) {
        $dataUpdate['c'] = [];
    }
    $dataUpdate['c'] = ['status' => $_GET['c'], 'data' => $dateNow, 'user' => $user];
    $update = true;
}

// TV
if (isset($_GET['t'])) {
    if (!isset($dataUpdate['t'])) {
        $dataUpdate['t'] = [];
    }
    $dataUpdate['t'] = ['status' => $_GET['t'], 'data' => $dateNow, 'user' => $user];
    $update = true;
}

$content = file_get_contents('content.log');
if (!empty($content) && $update) {
    $aContent = json_decode($content, true);
    $dataUpdate = array_merge($aContent, $dataUpdate);
}

if ($status) {
    $f = fopen("last-update-client.log", "w");
    fwrite($f, $dateNow);
    fclose($f);

    if (!empty($dataUpdate)) {
        $f = fopen("content.log", "w");
        fwrite($f, json_encode($dataUpdate));
        fclose($f);
    }
}

echo json_encode(['status' => $status]); exit;
