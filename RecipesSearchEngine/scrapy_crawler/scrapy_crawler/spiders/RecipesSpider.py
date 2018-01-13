import scrapy
from scrapy_crawler.items import *
from scrapy.selector import Selector

# run crawler - scrapy crawl recipes -o recipes.json

class RecipesSpider(scrapy.Spider):
    name = "recipes"
    start_urls = [
        'http://kulinar.bg/%D0%A0%D0%B5%D1%86D0B5D0%BF%D1%82D0B8_l.rl_gradus/.1.html',
        'http://www.24kitchen.bg/search/recipe?source=4'
    ]

    # more candidates: https://www.bonapeti.bg/recepti/, 

    def parse(self, response):
        if 'kulinar' in response.url:
            for href in response.xpath("//a/@href[contains(., '_l.r_i.')]"):
                full_url = response.urljoin(href.extract())
                yield scrapy.Request(full_url, callback=self.parse_kulinar_recipe_item)
            
            #for href in response.css('div.pagination a::attr(href)'):
            #    yield response.follow(href, callback=self.parse)

            # not wrorking
            #next_page = response.css('div.pagination a::attr(href)').extract_first()
            #if next_page is not None:
            #   next_page = response.urljoin(next_page)
            #   yield scrapy.Request(next_page, callback=self.parse)
            
        elif '24kitchen' in response.url:
            for href in response.xpath("//div[@class='image-wrapper']/a/@href"):
                full_url = response.urljoin(href.extract())
                yield scrapy.Request(full_url, callback=self.parse_24kitchen_recipe_item)

            #for href in response.css("ul.pager a::attr(href)"):
            #    yield response.follow(href, callback=self.parse)

            # not wrorking
            #next_page = response.css('div.pagination/a::attr(href)').extract_first()
            #if next_page is not None:
            #   next_page = response.urljoin(next_page)
            #   yield scrapy.Request(next_page, callback=self.parse)



    def parse_kulinar_recipe_item(self, response):
        #recipeLoader = RecipeItemLoader(item=RecipeItem(), response=response)
        #recipeLoader.add_xpath('name',
        #"//div[@class='recipeHead']/h1/span/text()")
        #recipeLoader.add_xpath('duration', "//span[@class='fs24
        #bold']/text()")
        #recipeLoader.add_xpath('servings', "//input[@class='fs24 openSans bold
        #alignCenter colorDef']/@value")
        #recipeLoader.add_xpath('category', "//span[@class='ml5
        #color3']/a/text()")
        #recipeLoader.add_xpath('difficulty', "count(//div[@class='recipeCap fl
        #full'])")
        #recipeLoader.add_xpath('image_url', "//div[@class='articleImg
        #overflow']/img/@src")
        #recipeLoader.add_xpath('user', "//div[@class='mb5
        #bold']/a/span[@class='ml5']/text()")

        item = RecipeItem()

        # Parse basic recipe data
        item['name'] = response.xpath("//div[@class='recipeHead']/h1/span/text()").extract_first()
        item['duration'] = response.xpath("//span[@class='fs24 bold']/text()").extract_first()
        item['servings'] = response.xpath("//input[@class='fs24 openSans bold alignCenter colorDef']/@value").extract_first()
        item['category'] = response.xpath("//span[@class='ml5 color3']/a/text()").extract_first()
        item['difficulty'] = response.xpath("count(//div[@class='recipeCap fl full'])").extract_first()
        item['rating'] = response.xpath("//span[@id='currentRatingContainer']/text()").extract_first()
        item['image_url'] = response.xpath("//div[@class='articleImg overflow']/img/@src").extract_first()
        item['user'] = response.xpath("//div[@class='mb5 bold']/a/span[@class='ml5']/text()").extract_first()
        item['ingredients'] = []
        item['comments'] = []
        item['url'] = response.url

        # Parse duration bound
        duration_bound = item['duration'].split(' ')[0]
        if duration_bound in ['>', '<']:
            item['duration_bound'] = duration_bound
        else:
             item['duration_bound'] = ""

        # Parse instructions data
        instructions = list()
        #instructions_data = response.xpath("//li[@class='item mb15 relative
        #fs14 articleText']")
        instructions_data = response.xpath("//li[@class='item mb15 relative fs14 articleText']")
        for instruction in instructions_data:
            #instruction_inner_data = ' '.join(instruction)
            instruction_inner_data = ' '.join(instruction.xpath("descendant-or-self::*/text()").extract()).lstrip().rstrip().strip('\n\n').replace("\n", "")
            instructions.append(instruction_inner_data)
        item['instructions'] = ' \n'.join(instructions)

        # Parse comments data
        comments = list()

        #comments_data = response.xpath("//span[@class='_5mdd']")
        #for comment in comments_data:
        #    comment_inner_data = comment.xpath("text()").extract()
        #    comments.append(comment_inner_data)

        comments_data = response.xpath("//div[@class='boxContent fs14']")
        for comment in comments_data:
            comment_inner_data = comment.xpath("text()").extract()
            comments.append(comment_inner_data)
        item['comments'] = comments

        # Parse ingredients data
        ingredients = list()
        ingredient_inner_data = IngredientItem()
        #ingredientLoader = IngredientItemLoader(item=IngredientItem(),
        #response=response)
        ingredients_data = response.xpath("//div[@class='item mb20 fs14 color3']")
        #quantities =
        #response.xpath("//span[@class='productQuantities']/text()").extract()
        #units = response.xpath("//span[@class='productItem mr20 colorDef
        #bold']/text()").extract()
        #names = response.xpath("//a[@class='color3
        #productName']/text()").extract()
        for ingredient in ingredients_data:
            ingredient_inner_data = {}

            quantity = ingredient.xpath("span/span[@class='productQuantities']/text()").extract()[0]
            unit = ingredient.xpath("span[@class='productItem mr20 colorDef bold']/text()").extract()[0]
            name = ingredient.xpath("a[@class='color3 productName']/text()").extract()[0].lstrip().rstrip
        

            #ingredientLoader.add_value('quantity', quantities[index])
            ingredient_inner_data['quantity'] = quantity

            #ingredientLoader.add_value('unit', units[index])
            ingredient_inner_data['unit'] = unit

            #ingredientLoader.add_value('name', names[index])
            ingredient_inner_data['name'] = name

            ingredient_inner_data['unstructured_data'] = quantity + ' ' + unit + ' ' + name

            ingredient_inner_data['common'] = "0"

            ingredients.append(ingredient_inner_data)
            #ingredient_info = ingredientLoader.load_item()
        item['ingredients'] = ingredients
            #ingredient.append(ingredient_info)

        #recipeLoader.add_value('ingredients', ingredients)
        #loader.add_value('ingredients', self.parse_ingredient_item(response))
        #return recipeLoader.load_item()

        yield item

        #item = RecipeItem()
        #item['name'] =
        #response.xpath("//div[@class='recipeHead']/h1/span/text()").extract_first()
        #item['duration'] = response.xpath("//span[@class='fs24
        #bold']/text()").extract_first()
        #item['servings'] = response.xpath("//input[@class='fs24 openSans bold
        #alignCenter colorDef']/@value").extract_first()
        #item['category'] = response.xpath("//span[@class='ml5
        #color3']/a/text()").extract_first()
        #item['difficulty'] = response.xpath("count(//div[@class='recipeCap fl
        #full'])").extract_first()
        #item['image_url'] = response.xpath("//div[@class='articleImg
        #overflow']/img/@src").extract_first()
        #item['user'] = response.xpath("//div[@class='mb5
        #bold']/a/span[@class='ml5']/text()").extract_first()
        #yield item

    #def parse_ingredient_item(self, response):
    #    loader = IngredientItemLoader(item=IngredientItem(),
    #    response=response)
    #    loader.add_xpath('name', "")
    #    return loader.load_item()

    def parse_24kitchen_recipe_item(self, response):
        item = RecipeItem()

        # Parse basic recipe data
        item['name'] = response.xpath("//h1[@class='fn title']/text()").extract_first()
        item['duration'] = response.xpath("//div[@class='field-cook-time cookTime']/text()").extract_first()
        item['servings'] = response.xpath("//input[@class='form-text ajax-processed']/@value").extract_first()
        item['category'] = response.xpath("//span[@class='field-content']/a[contains(@href,'course')]/text()").extract_first()
        item['difficulty'] = response.xpath("count(//span[@class='field-content']/a[contains(@href,'course')]/text())").extract_first()
        stars = response.xpath("//a[@class='rating_star']/text()").extract()
        item['rating'] = str(stars.count(u'\u2605'))
        item['image_url'] = response.xpath("//div[@class='file file-image file-image-jpeg']/img/@src").extract_first()
        item['user'] = response.xpath("//span[@class='author']/text()").extract_first()
        item['comments'] = []
        item['url'] = response.url

        # Parse duration bound
        duration_bound = item['duration'].split(' ')[0]
        if duration_bound in ['>', '<']:
            item['duration_bound'] = duration_bound
        else:
             item['duration_bound'] = ""


        # Parse instructions
        #instructions_text = response.xpath("//div[@class='field-item-child instructions']/text()").extract() - for lists
        instructions_text = ' \n'.join(response.xpath("//div[@class='field-item-child instructions']/text()").extract()).lstrip().rstrip().strip('\n') 
        if instructions_text == "":
            instructions = list()
            #instructions_text = instructions_text + ' \n'.join(response.xpath("//div[@class='field-item-child instructions']/descendant-or-self::/text()").extract())
            instructions_data = response.xpath("//div[@class='field-item-child instructions']")
            for instruction in instructions_data:
                #instruction_inner_data = instruction.xpath("//div/text()").extract().lstrip().rstrip().strip('\n') - not good
                instruction_inner_data = ' \n'.join(instruction.xpath("descendant-or-self::*/text()").extract()).lstrip().rstrip().strip('\n')
                #instruction_inner_data = instruction.xpath("descendant-or-self::*/text()").extract() - for lists
                instructions.append(instruction_inner_data)
            instructions_text = instructions[0]

        item['instructions'] = instructions_text


        # Parse comments data
        item['comments'] = response.xpath("//span[@class='_5mdd']/text()").extract()


        # Parse ingredients data
        ingredients = list()
        ingredient_inner_data = IngredientItem()
        ingredients_data = response.xpath("//span[@class='ingredient']")

        for ingredient in ingredients_data:
            ingredient_inner_data = {}

            quantity = ingredient.xpath("span[@class='amount']/text()").extract_first()
            if  quantity is None:
                quantity = ""
            unit = ingredient.xpath("span[2]/text()").extract_first()
            if  unit is None:
                unit = ""
            name = ingredient.xpath("text()").extract()
            name = [item.lstrip().rstrip() for item in name if item != u'\xa0'][0]
        
            ingredient_inner_data['quantity'] = quantity
            ingredient_inner_data['unit'] = unit
            ingredient_inner_data['name'] = name
            ingredient_inner_data['unstructured_data'] = quantity + ' ' + unit + ' ' + name
            ingredient_inner_data['common'] = "0"
            ingredients.append(ingredient_inner_data)

      
        item['ingredients'] = ingredients
        
        yield item
