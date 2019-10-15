import scrapy
from funcionarios_prov_cba.items import FuncionariosProvCbaItem


class FuncionariosCordobaProvinciaSpider(scrapy.Spider):
    name = "funcionarios"

    bad_urls = ['http://www.upc.edu.ar']

    def start_requests(self):
        urls = [
            'http://www.cba.gov.ar/reparticiones/',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.logger.info(' *** BUSCANDO MINISTERIOS **** ')

        for reparticion in response.xpath('//ul[@class="sub-menu"]/li'):
            rep_nombre = reparticion.xpath('a/text()').get()
            rep_url = reparticion.xpath('.//@href').get()
            # esta caida y no tiene la estructura que buscamos
            if rep_url in self.bad_urls:
                self.logger.info('Ignorando ministerio {}'.format(rep_url))
            else:
                next_page = response.urljoin(rep_url)
                yield scrapy.Request(next_page, callback=self.parse_ministerio, meta={'web_url': rep_url})

    def parse_ministerio(self, response):

        ministerio = response.xpath('//header/h1/text()').get()

        self.logger.info(' *** INICIANDO {}**** '.format(ministerio))

        # div class fotoaut -> img src foto del funcionario
        foto = response.xpath('//div[@class="fotoaut"]/img/@src').extract_first()

        # ver la organica del ministerio
        organica = response.xpath('//section[@class="barra-lateral"]/a[text()="Estructura Orgánica"]/@href').get()

        if organica is None:
            self.logger.info('********\nNo hay organica en {}\n********'.format(ministerio))
        else:
            self.logger.info('Organica en {}'.format(organica))

            # esta caida y no tiene la estructura que buscamos
            if organica in self.bad_urls:
                self.logger.info('Ignorando dentro de ministerio {}'.format(rep_url))
            else:
                next_page = response.urljoin(organica)
                yield scrapy.Request(
                    next_page,
                    callback=self.parse_estructura_ministerio,
                    meta={'ministerio': ministerio, 'web_url': response.meta['web_url']}
                )

    def parse_estructura_ministerio(self, response):
        self.logger.info(' *** EN ESTRUCTURA MINISTERIO {} **** '.format(response.meta['ministerio']))

        autoridades = response.xpath('//section[@class="esencial"]')

        for autoridad in autoridades:

            a2 = autoridad.xpath('.//div')

            # hay un label + h4 donde se ve el nombre del cargo y ...
            a3b = a2.xpath('.//label')
            cargo_generico = a3b.xpath('.//h4/text()').extract()[1]

            # un div con el nombre especifico, por ejemplo "Directora" en las mujeres
            a3 = a2.xpath('.//div')

            func = a3.xpath('.//h3/text()').extract_first()
            cargo_ocupado = a3.xpath('.//h5/text()').extract_first()

            # div class fotoaut -> img src foto del funcionario
            foto = a3.xpath('.//div[@class="fotoaut"]/img/@src').extract_first()

            # aparece a veces un link (quizas sea nuevo)
            # div class acceder_largue -> a href link fijo a este funcionario solo
            web_url = a3.xpath('.//div[@class="acceder_largue"]/a/@href').extract_first()
            if web_url in self.bad_urls:
                self.logger.info('Ignorando funcionario {}'.format(rep_url))
                web_url = ''
            if func is None:
                err = 'Autoridad no identificada: {} en {}. Cargo: {} / {}'.format(a3,
                                                                                response.meta['web_url'],
                                                                                cargo_generico,
                                                                                cargo_ocupado)
                # raise ValueError(err)
                self.logger.info(err)
                func = ''  # no hay funcionario designado

            func = func.replace('\t', '').replace('\r', '').replace('\n', '')
            cargo_generico = cargo_generico.replace('\t', '').replace('\r', '').replace('\n', '')
            cargo_ocupado = cargo_ocupado.replace('\t', '').replace('\r', '').replace('\n', '')
            funcionario = {'funcionario': func,
                            'cargo_generico': cargo_generico,
                            'cargo_ocupado': cargo_ocupado,
                            'ministerio': response.meta['ministerio'],
                            'web_url': web_url,  # response.meta['web_url'],
                            'foto_url': [] if foto is None else [foto]
                            }
            # yield funcionario
            yield FuncionariosProvCbaItem(**funcionario)
